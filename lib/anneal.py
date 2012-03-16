#!/usr/bin/env python

# Python module for simulated annealing - anneal.py - v1.0 - 2 Sep 2009
# 
# Copyright (c) 2009, Richard J. Wagner <wagnerr@umich.edu>
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
This module performs simulated annealing to find a state of a system that
minimizes its energy.

An example program demonstrates simulated annealing with a traveling
salesman problem to find the shortest route to visit the twenty largest
cities in the United States.
"""

# How to optimize a system with simulated annealing:
# 
# 1) Define a format for describing the state of the system.
# 
# 2) Define a function to calculate the energy of a state.
# 
# 3) Define a function to make a random change to a state.
# 
# 4) Choose a maximum temperature, minimum temperature, and number of steps.
# 
# 5) Set the annealer to work with your state and functions.
# 
# 6) Study the variation in energy with temperature and duration to find a
# productive annealing schedule.
# 
# Or,
# 
# 4) Run the automatic annealer which will attempt to choose reasonable values
# for maximum and minimum temperatures and then anneal for the allotted time.

import copy, math, random, sys, time, re

def round_figures(x, n):
	"""Returns x rounded to n significant figures."""
	return round(x, int(n - math.ceil(math.log10(abs(x)))))

def time_string(seconds):
	"""Returns time in seconds as a string formatted HHHH:MM:SS."""
	s = int(round(seconds))  # round to nearest second
	h, s = divmod(s, 3600)   # get hours and remainder
	m, s = divmod(s, 60)     # split remainder into minutes and seconds
	return '%4i:%02i:%02i' % (h, m, s)

class Annealer:
	"""Performs simulated annealing by calling functions to calculate
	energy and make moves on a state.  The temperature schedule for
	annealing may be provided manually or estimated automatically.
	"""
	def __init__(self, energy, move):
		self.energy = energy  # function to calculate energy of a state
		self.move = move      # function to make a random change to a state
	
	def anneal(self, state, Tmax, Tmin, steps, updates=0):
		"""Minimizes the energy of a system by simulated annealing.
		
		Keyword arguments:
		state -- an initial arrangement of the system
		Tmax -- maximum temperature (in units of energy)
		Tmin -- minimum temperature (must be greater than zero)
		steps -- the number of steps requested
		updates -- the number of updates to print during annealing
		
		Returns the best state and energy found."""
		
		step = 0
		start = time.time()
		
		def update(T, E, acceptance, improvement):
			"""Prints the current temperature, energy, acceptance rate,
			improvement rate, elapsed time, and remaining time.
			
			The acceptance rate indicates the percentage of moves since the last
			update that were accepted by the Metropolis algorithm.  It includes
			moves that decreased the energy, moves that left the energy
			unchanged, and moves that increased the energy yet were reached by
			thermal excitation.
			
			The improvement rate indicates the percentage of moves since the
			last update that strictly decreased the energy.  At high
			temperatures it will include both moves that improved the overall
			state and moves that simply undid previously accepted moves that
			increased the energy by thermal excititation.  At low temperatures
			it will tend toward zero as the moves that can decrease the energy
			are exhausted and moves that would increase the energy are no longer
			thermally accessible."""
			
			elapsed = time.time() - start
			if step == 0:
				print ' Temperature        Energy    Accept   Improve     Elapsed   Remaining'
				print '%12.2f  %12.2f                      %s            ' % \
					(T, E, time_string(elapsed) )
			else:
				remain = ( steps - step ) * ( elapsed / step )
				print '%12.2f  %12.2f  %7.2f%%  %7.2f%%  %s  %s' % \
					(T, E, 100.0*acceptance, 100.0*improvement,
						time_string(elapsed), time_string(remain))
		
		# Precompute factor for exponential cooling from Tmax to Tmin
		if Tmin <= 0.0:
			print 'Exponential cooling requires a minimum temperature greater than zero.'
			sys.exit()
		Tfactor = -math.log( float(Tmax) / Tmin )
		
		# Note initial state
		T = Tmax
		E = self.energy(state)
		prevState = copy.deepcopy(state)
		prevEnergy = E
		bestState = copy.deepcopy(state)
		bestEnergy = E
		trials, accepts, improves = 0, 0, 0
		if updates > 0:
			updateWavelength = float(steps) / updates
			update(T, E, None, None)
		
		# Attempt moves to new states
		while step < steps:
			step += 1
			T = Tmax * math.exp( Tfactor * step / steps )
			self.move(state)
			E = self.energy(state)
			dE = E - prevEnergy
			trials += 1
			if dE > 0.0 and math.exp(-dE/T) < random.random():
				# Restore previous state
				state = copy.deepcopy(prevState)
				E = prevEnergy
			else:
				# Accept new state and compare to best state
				accepts += 1
				if dE < 0.0:
					improves += 1
				prevState = copy.deepcopy(state)
				prevEnergy = E
				if E < bestEnergy:
					bestState = copy.deepcopy(state)
					bestEnergy = E
			if updates > 1:
				if step // updateWavelength > (step-1) // updateWavelength:
					update(T, E, float(accepts)/trials, float(improves)/trials)
					trials, accepts, improves = 0, 0, 0
		
		# Return best state and energy
		return bestState, bestEnergy
	
	def auto(self, state, minutes, steps=2000):
		"""Minimizes the energy of a system by simulated annealing with
		automatic selection of the temperature schedule.
		
		Keyword arguments:
		state -- an initial arrangement of the system
		minutes -- time to spend annealing (after exploring temperatures)
		steps -- number of steps to spend on each stage of exploration
		
		Returns the best state and energy found."""
		
		def run(state, T, steps):
			"""Anneals a system at constant temperature and returns the state,
			energy, rate of acceptance, and rate of improvement."""
			E = self.energy(state)
			prevState = copy.deepcopy(state)
			prevEnergy = E
			accepts, improves = 0, 0
			for step in range(steps):
				self.move(state)
				E = self.energy(state)
				dE = E - prevEnergy
				if dE > 0.0 and math.exp(-dE/T) < random.random():
					state = copy.deepcopy(prevState)
					E = prevEnergy
				else:
					accepts += 1
					if dE < 0.0:
						improves += 1
					prevState = copy.deepcopy(state)
					prevEnergy = E
			return state, E, float(accepts)/steps, float(improves)/steps
		
		step = 0
		start = time.time()
		
		print 'Attempting automatic simulated anneal...'
		
		# Find an initial guess for temperature
		T = 0.0
		E = self.energy(state)
		while T == 0.0:
			step += 1
			self.move(state)
			T = abs( self.energy(state) - E )
		
		print 'Exploring temperature landscape:'
		print ' Temperature        Energy    Accept   Improve     Elapsed'
		def update(T, E, acceptance, improvement):
			"""Prints the current temperature, energy, acceptance rate,
			improvement rate, and elapsed time."""
			elapsed = time.time() - start
			print '%12.2f  %12.2f  %7.2f%%  %7.2f%%  %s' % \
				(T, E, 100.0*acceptance, 100.0*improvement, time_string(elapsed))
		
		# Search for Tmax - a temperature that gives 98% acceptance
		state, E, acceptance, improvement = run(state, T, steps)
		step += steps
		while acceptance > 0.98:
			T = round_figures(T/1.5, 2)
			state, E, acceptance, improvement = run(state, T, steps)
			step += steps
			update(T, E, acceptance, improvement)
		while acceptance < 0.98:
			T = round_figures(T*1.5, 2)
			state, E, acceptance, improvement = run(state, T, steps)
			step += steps
			update(T, E, acceptance, improvement)
		Tmax = T
		
		# Search for Tmin - a temperature that gives 0% improvement
		while improvement > 0.0:
			T = round_figures(T/1.5, 2)
			state, E, acceptance, improvement = run(state, T, steps)
			step += steps
			update(T, E, acceptance, improvement)
		Tmin = T
		
		# Calculate anneal duration
		elapsed = time.time() - start
		duration = round_figures(int(60.0 * minutes * step / elapsed), 2)
		
		# Perform anneal
		print 'Annealing from %.2f to %.2f over %i steps:' % (Tmax, Tmin, duration)
		return self.anneal(state, Tmax, Tmin, duration, 20)

	# TODO: Make this work for arbitrary 
	# Returns the list of Triangles representing the objects in the
	#	given SVG group
def triangulate(tri):
	pointsString = tri.get_points()
	# Turn that string into a list of doubles
	splitString = re.findall('[-]*[0-9]+[.]*[0-9]+', pointsString)
	doubles = map(float, splitString)
	p1 = Point(doubles[0], doubles[1])
	p2 = Point(doubles[2], doubles[3])
	p3 = Point(doubles[4], doubles[5])
	tri = Triangle(p1, p2, p3)
	return [tri]

# Data structure to hold a group from the SVG file
# Note: Element position in the SVG does not matter because these
#	will be inserted into the final SVG in any order, does not matter
class Group:
	def __init__(self, tri, pos, height, width):
		# Initial rotation is 0
		self.rot = 0.0
		# Initial translation is 0
		self.trans = Point(0.0, 0.0)
		# This elements original position in the parent SVG
		self.pos = pos
		# List of triangles which approximate the original positions of
		#	the objects in the group
		self.itris = triangulate(tri)
		# No change in initial position
		self.ctris = self.itris
		self.bheight = height
		self.bwidth = width

# Data structure to define a triangle via three points
class Triangle:
	def __init__(self, p1, p2, p3):
		self.p1 = p1
		self.p2 = p2
		self.p3 = p3

# Data structure to hold a point location
class Point:
	def __init__(self, x, y):
		self.x = x
		self.y = y