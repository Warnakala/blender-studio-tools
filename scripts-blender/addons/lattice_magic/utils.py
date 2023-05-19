import bpy
from mathutils import Vector
from typing import List, Tuple

def clamp(val, _min=0, _max=1) -> float or int:
	if val < _min:
		return _min
	if val > _max:
		return _max
	return val

def get_lattice_vertex_index(lattice: bpy.types.Lattice, xyz: List[int], do_clamp=True) -> int:
	"""Get the index of a lattice vertex based on its position on the XYZ axes."""

	# The lattice vertex indicies start in the -Y, -X, -Z corner, 
	# increase on X+, then moves to the next row on Y+, then moves up on Z+.
	res_x, res_y, res_z = lattice.points_u, lattice.points_v, lattice.points_w
	x, y, z = xyz[:]
	if do_clamp:
		x = clamp(x, 0, res_x)
		y = clamp(y, 0, res_y)
		z = clamp(z, 0, res_z)

	assert x < res_x and y < res_y and z < res_z, "Error: Lattice vertex xyz index out of bounds"

	index = (z * res_y*res_x) + (y * res_x) + x
	return index

def get_lattice_vertex_xyz_position(lattice: bpy.types.Lattice, index: int) -> (int, int, int):
	res_x, res_y, res_z = lattice.points_u, lattice.points_v, lattice.points_w

	x = 0
	remaining = index
	z = int(remaining / (res_x*res_y))
	remaining -= z*(res_x*res_y)
	y = int(remaining / res_x)
	remaining -= y*res_x
	x = remaining # Maybe need to add or subtract 1 here?

	return (x, y, z)

def get_lattice_point_original_position(lattice: bpy.types.Lattice, index: int) -> Vector:
	"""Reset a lattice vertex to its original position."""
	start_vec = Vector((-0.5, -0.5, -0.5))
	if lattice.points_u == 1:
		start_vec[0] = 0
	if lattice.points_v == 1:
		start_vec[1] = 0
	if lattice.points_w == 1:
		start_vec[2] = 0

	unit_u = 1/(lattice.points_u-0.99)
	unit_v = 1/(lattice.points_v-0.99)
	unit_w = 1/(lattice.points_w-0.99)

	unit_vec = Vector((unit_u, unit_v, unit_w))
	xyz_vec = Vector(get_lattice_vertex_xyz_position(lattice, index))

	return start_vec + xyz_vec*unit_vec

def simple_driver(owner: bpy.types.ID, driver_path: str, target_ob: bpy.types.Object, data_path: str, array_index=-1) -> bpy.types.Driver:
	if array_index > -1:
		owner.driver_remove(driver_path, array_index)
		driver = owner.driver_add(driver_path, array_index).driver
	else:
		owner.driver_remove(driver_path)
		driver = owner.driver_add(driver_path).driver
	
	driver.expression = 'var'
	var = driver.variables.new()
	var.targets[0].id = target_ob
	var.targets[0].data_path = data_path

	return driver


def bounding_box(points) -> Tuple[Vector, Vector]:
	""" Return two vectors representing the lowest and highest coordinates of 
		a the bounding box of the passed points.
	"""

	lowest = points[0].copy()
	highest = points[0].copy()
	for p in points:
		for i in range(len(p)):
			if p[i] < lowest[i]:
				lowest[i] = p[i]
			if p[i] > highest[i]:
				highest[i] = p[i]

	return lowest, highest

def bounding_box_center(points) -> Vector:
	"""Find the bounding box center of some points."""
	bbox_low, bbox_high = bounding_box(points)
	return bbox_low + (bbox_high-bbox_low)/2

def bounding_box_center_of_objects(objects) -> Vector:
	"""Find the bounding box center of some objects."""
	all_points = []
	for o in objects:
		for p in o.bound_box:
			all_points.append(o.matrix_world @ Vector(p))
	return bounding_box_center(all_points)