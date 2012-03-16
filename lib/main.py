from pysvg import parser
from pysvg.structure import *
from anneal import *
import re, math
from random import choice

# TODO How do I get the number of elements in an SVG?

# Take an svg and return a list of all Groups in it
def grouper(svg):
    height = float(re.findall('[0-9]+', svg.getAttribute('height'))[0])
    width = float(re.findall('[0-9]+', svg.getAttribute('width'))[0])
    groups = []
    i = 0
    for x in svg._subElements:
        i = i + 1
        if (x.__class__.__name__ == "polygon"):
            groups = groups + [Group(x, i, height, width)]
    return groups

# Take the original SVG and the Group to be dumped
def dumper(svg, group):
    # Create an empty group
    gr = g()
    # group.trans.x, group.trans.y
    transString = "rotate(" + str(group.rot) + ") translate(" + str(group.trans.x) + "," + str(group.trans.y) + ")"
    gr.set_transform(transString)
    gr.addElement(svg.getElementAt(group.pos - 1))
    return gr

# Take a group and an x,y translation and update the triangle points
def translateGroup(group, x, y):
    # Update the Group translation value
    group.trans = Point(group.trans.x + x, group.trans.y + y)
    # Iterate through the triangles in the group 
    for tri in group.ctris:
        tri.p1.x += x
        tri.p2.x += x
        tri.p3.x += x
        tri.p1.y += y
        tri.p2.y += y
        tri.p3.y += y

# Rotate a group's triangles about the origin
def rotateGroup(group, th):
    # Update the Group rotate value
    group.rot += th
    # Iterate through the triangles in the group
    for tri in group.ctris:
        # TODO: Reduce code duplication here
        x = tri.p1.x
        tri.p1.x = x*math.cos(th*math.pi/180) - tri.p1.y*math.sin(th*math.pi/180)
        tri.p1.y = x*math.sin(th*math.pi/180) + tri.p1.y*math.cos(th*math.pi/180)
        
        x = tri.p2.x
        tri.p2.x = x*math.cos(th*math.pi/180) - tri.p2.y*math.sin(th*math.pi/180)
        tri.p2.y = x*math.sin(th*math.pi/180) + tri.p2.y*math.cos(th*math.pi/180)
        
        x = tri.p3.x
        tri.p3.x = x*math.cos(th*math.pi/180) - tri.p3.y*math.sin(th*math.pi/180)
        tri.p3.y = x*math.sin(th*math.pi/180) + tri.p3.y*math.cos(th*math.pi/180)

# Update the triangles of a group with a desired rotation and translation
def moveGroup(group, rot, xtrans, ytrans):
    translateGroup(group, xtrans, ytrans)
    rotateGroup(group, rot)

# Take a group and return 1 if it is off the board, 0 if it is within the board
def off_board_check(group):
    height = group.bheight
    width = group.bwidth
    xs = []
    ys = []
    # Iterate through all triangles
    for y in group.ctris:
        xs = xs + [y.p1.x] + [y.p2.x] + [y.p3.x]
        ys = ys + [y.p1.y] + [y.p2.y] + [y.p3.y]
    # Get the maximum and minimum points
    minx = min(xs)
    miny = min(ys)
    maxx = max(xs)
    maxy = max(ys)
    # Negative positions are not allowed
    if (minx < 0 or miny < 0 or maxx < 0 or maxy < 0):
        return 1
    # Positions greater than the board are not allowed
    if (maxx > width or maxy > height):
        return 1
    return 0

# Calculate the total rectangular area required to consume all groups
def rectArea(groups):
    xs = []
    ys = []
    # Iterate through all groups
    for x in groups:
        # Iterate through all triangles
        for y in x.ctris:
            xs = xs + [y.p1.x] + [y.p2.x] + [y.p3.x]
            ys = ys + [y.p1.y] + [y.p2.y] + [y.p3.y]
    minx = min(xs)
    miny = min(ys)
    maxx = max(xs)
    maxy = max(ys)
    length = maxx - minx
    width = maxy - miny
    return length*width

# Calculate E = rectangular area consumed + overlap penalty
def state_energy(groups):
    E = rectArea(groups)
    # FIXME: Add overlap penalties
    return E

# Take a Group and produce a random shift in it such that
#    it is not outside the given artboard boundary
def group_move(group, damper):
    new = copy.deepcopy(group)
    # Maximum move length
    # TODO: This hard coded number needs to be changed to the 
    #    total area of all the triangles
    lmax = math.sqrt(1000/math.pi)
    # Randomly choose a degree to rotate
    dr = random.uniform(-180.0,180.0)/damper
    # Randomly choose values to translate
    # TODO: Why do I never produce any negative values here?
    dx = (2*random.uniform(0.0, lmax) - lmax)/damper
    dy = (2*random.uniform(0.0, lmax) - lmax)/damper
    # Make the move
    moveGroup(new, dr, dx, dy)
    # print("new trans = " + str(new.trans.x))
    # If something is off the board, then try again
    if (off_board_check(new) == 1):
        damper += 2.0
        # print "Found a prob."
        # Reset to original to try again
        # print("saved trans = " + str(group.trans.x))
        return group_move(group, damper)
    else:
        # If everything is on the board, then make the change
        return new

# Randomly move one of the groups in the given state
def state_move(groups):
    # Randomly choose one of the groups
    i = random.randint( 0, len(groups)-1 )
    groups[i] = group_move(groups[i], 1.0)

def main():
    input = sys.argv[1]
    output = sys.argv[2]
    mySVG = parser.parse(input)
    height = float(re.findall('[0-9]+', mySVG.getAttribute('height'))[0])
    width = float(re.findall('[0-9]+', mySVG.getAttribute('width'))[0])
    # Get the height and width of the SVG art board

    # Put all the triangles into the Group data structure
    groups = grouper(mySVG)

    print rectArea(groups)

    # Run simulated annealing on the set of groups
    # Define my annealer
    # annealer = Annealer(state_energy, state_move)
    # groups, e = annealer.auto(groups, 4)

    # Create the output SVG
    destSVG = svg()
    # Set the width and height of this SVG
    destSVG.setAttribute("height", height)
    destSVG.setAttribute("width", width)
    # Dump all triangles into the destination SVG
    for x in groups:
        destSVG.addElement(dumper(mySVG, x))
    # Will overwrite any existing file
    destSVG.save(output)

if __name__ == '__main__': 
    main()

# TODO
# overlap(Groups) takes a set of Groups and returns the total area of overlap
#    between them.  Uses CCW method.