import sys
import math
from PIL import Image
from typing import List, Union
from potrace import Bitmap, POTRACE_TURNPOLICY_MINORITY, BezierSegment, CornerSegment, Curve  # pip `potracer` library

FILE_INPUT = "glasses_mask.png"
# STEPS IN GIMP TO MAKE glasses_mask.png FROM MY 2 INPUT IMAGES:
# - make a tinted layer and non-tinted layer
# - set the mode of the second one to difference
# - maybe there was another step here?
# - gaussian blur filter default settings (1.5 x 1.5)
# - threshold green 24
# - clean up edges
# - invert
# - color to alpha
# - invert
# - merge layer down
# - resize canvas to add padding
# - gaussian blur
# - threshold Luminance 250

ADD_DOTS = False
# ADD_DOTS = True

DOT_COLORS = ["red", "green", "blue"]

LENS_COLOR = "#000000AA"

# Colors pattern
COLORS = [
	"#f7c45b", "#fd8a52", "#fd664b", "#f65d87", "#9e6097", "#b77fb7", "#705e97", "#5fb1f8", "#70c9fe", "#87ddfd", "#4bc681", "#70d975", "#9fe16e", "#edf55f"
]
COLORS.reverse()

# TODO: should fix this to all be based on the center point. need to have y1  and y2 too probably to be set to the bridge height. ideally, rotation and resizing has its origin so orange is always in center.
# Gradient configuration
SLICE_WIDTH = 43  # Width of each color slice in the gradient
TRANSITION_WIDTH = 0  # Width of transitions between colors
GRADIENT_ANGLE = 45  # Angle of the gradient
GRADIENT_OFFSET = -30  # Offset to shift colors

# chat gpt was helpful for this one. (Oct 24th 2024)
def create_gradient_def(colors: List[str], slice_width: int, transition_width: int, angle: int, offset: int, viewbox_width: int):
	# Calculate the total width of the gradient pattern (one full cycle of the colors)
	offset += (viewbox_width // 2)

	color_section_width = len(colors) * (slice_width + transition_width)

	gradient_steps = []
	position = 0

	colors.append(colors[0])

	for i, color in enumerate(colors):
		start_pos = position / color_section_width
		end_pos = (position + slice_width) / color_section_width

		if i != len(colors) - 1:
			gradient_steps.append(f'<stop offset="{start_pos:.2f}" stop-color="{color}" />')
		gradient_steps.append(f'<stop offset="{end_pos:.2f}" stop-color="{color}" />')

		position += slice_width + transition_width

	# SVG gradient definition with repeating setup
	gradient_def = f'''
	<defs>
		<linearGradient id="rainbowGradient" gradientUnits="userSpaceOnUse" spreadMethod="repeat"
						gradientTransform="rotate({angle})"
						x1="{offset}" y1="0" x2="{color_section_width + offset}" y2="0">
			{"".join(gradient_steps)}
		</linearGradient>
	</defs>
	'''
	return gradient_def





# # Calculate the Euclidean distance between two points
# def distance(p1, p2) -> float:
# 	return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

# # Linearly interpolate between two points
# def lerp(p1, p2, t: float):
# 	return type(p1)(x=p1.x * (1 - t) + p2.x * t, y=p1.y * (1 - t) + p2.y * t)

# # Check if two Bézier segments can be merged
# def can_merge(segment1: BezierSegment, segment2: BezierSegment, dist_tol: float = 2, angle_tol: float = 0.1) -> bool:
# 	# Check distance tolerance (end of the first segment to start of the second)
# 	if distance(segment1.end_point, segment2.c1) > dist_tol:
# 	    return False

# 	# Calculate the tangents
# 	tangent1 = (segment1.c2.x - segment1.end_point.x, segment1.c2.y - segment1.end_point.y)
# 	tangent2 = (segment2.c2.x - segment2.c1.x, segment2.c2.y - segment2.c1.y)

# 	# Normalize the tangents
# 	len1 = math.sqrt(tangent1[0] ** 2 + tangent1[1] ** 2)
# 	len2 = math.sqrt(tangent2[0] ** 2 + tangent2[1] ** 2)
# 	if len1 == 0 or len2 == 0:
# 		return False

# 	# Dot product to check angle tolerance (are tangents nearly collinear, either direction?)
# 	dot_product = (tangent1[0] * tangent2[0] + tangent1[1] * tangent2[1]) / (len1 * len2)
	
# 	# Check if the absolute dot product is close to 1, allowing for parallel vectors in both directions
# 	return abs(abs(dot_product) - 1) < angle_tol


# # Merge two Bézier segments by adjusting control points
# def merge_segments(segment1: BezierSegment, segment2: BezierSegment) -> BezierSegment:
# 	# We'll create a new BezierSegment that combines segment1 and segment2
# 	# The new segment's control points are a blend between the two original segments
# 	new_c1 = lerp(segment1.c1, segment2.c1, 0.5)  # Average of the control points
# 	new_c2 = lerp(segment1.c2, segment2.c2, 0.5)  # Average of the control points
# 	new_end_point = segment2.end_point  # Use the end point of the second segment

# 	# Create a new BezierSegment with the merged control points
# 	new_segment = BezierSegment(segment1._segment)  # Copy the original segment
# 	new_segment._segment.c[0] = segment1.c1  # Keep the first control point
# 	new_segment._segment.c[1] = new_c2  # Use the new blended control point
# 	new_segment._segment.c[2] = new_end_point  # End at the second segment's end point

# 	return new_segment

# def simplify_curve(curve: Curve, dist_tol: float = 2, angle_tol: float = 0.1) -> Curve:
# 	if not curve.segments:
# 		return curve  # Return immediately if there are no segments

# 	new_segments = []
# 	current_segment = curve.segments[0]  # Start with the first segment

# 	for next_segment in curve.segments[1:]:
# 		if isinstance(current_segment, BezierSegment) and isinstance(next_segment, BezierSegment):
# 			if can_merge(current_segment, next_segment, dist_tol, angle_tol):
# 				# Merge the current and next segments into one
# 				current_segment = merge_segments(current_segment, next_segment)
# 				# print("merging")
# 			else:
# 				# If they can't be merged, append the current segment to the result
# 				new_segments.append(current_segment)
# 				current_segment = next_segment
# 		else:
# 			# Corner segments or unmergeable segments are directly added to the result
# 			new_segments.append(current_segment)
# 			current_segment = next_segment

# 	# Add the final segment (whether it's been merged or not)
# 	new_segments.append(current_segment)

# 	# Replace the original segments list in place with the simplified segments
# 	curve[:] = new_segments  # Replace segments in the original curve

# 	return curve




def file_to_svg(filename: str):
	try:
		image = Image.open(filename)
	except IOError:
		print("Image (%s) could not be loaded." % filename)
		return
	bm = Bitmap(image, blacklevel=0.5)
	# bm.invert()
	plist = bm.trace(
		turdsize=2, # - suppress speckles of up to this size (default 2)
		turnpolicy=POTRACE_TURNPOLICY_MINORITY,
		alphamax=1, # - curve optimization tolerance (default 0.2)
		opticurve=False,
		opttolerance=.2,
	)

	with open(f"{filename}.svg", "w+") as fp:
		fp.write(
			f'''<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{image.width}" height="{image.height}" viewBox="0 0 {image.width} {image.height}">''')


		gradient_def = create_gradient_def(COLORS, SLICE_WIDTH, TRANSITION_WIDTH, GRADIENT_ANGLE, GRADIENT_OFFSET, image.width)

		fp.write(gradient_def)
		
		lens_parts = []
		parts = []
		dots = []
		for i, curve in enumerate(plist):
			# curve = simplify_curve(curve, 8, 0.001) # THIS IS PRETTY GOOD, BUT I THINK IMMA KEEP ORIGINAL
			fs = curve.start_point
			print(f"Curve #{i}:")
			print(f"- Segments: {len(curve.segments)}")
			curve_parts = []
			curve_parts.append(f"M{fs.x},{fs.y}")
			for segment in curve.segments:
				if segment.is_corner:
					a = segment.c
					b = segment.end_point
					curve_parts.append(f"L{a.x},{a.y}L{b.x},{b.y}")
				else:
					a = segment.c1
					b = segment.c2
					c = segment.end_point
					curve_parts.append(f"C{a.x},{a.y} {b.x},{b.y} {c.x},{c.y}")

				# Add a colored dot at the end point for each segment
				color = DOT_COLORS[i % len(DOT_COLORS)]  # Cycle through the colors
				dots.append(f'<circle cx="{segment.end_point.x}" cy="{segment.end_point.y}" r="8" fill="{color}" />')

			curve_parts.append("z")
			parts.extend(curve_parts)
			if i != 0:
				lens_parts.extend(curve_parts)

			
		
		# fp.write(f'<path stroke="none" fill="black" fill-rule="evenodd" d="{"".join(parts)}"/>')
		fp.write(f'<path stroke="none" fill="url(#rainbowGradient)" d="{"".join(parts)}"/>')
		fp.write(f'<path stroke="{LENS_COLOR}" stroke-width="1" fill="{LENS_COLOR}" fill-rule="evenodd" d="{"".join(lens_parts)}"/>')

		if ADD_DOTS: 
			# Add the dots to the SVG
			fp.write("\n".join(dots))

		fp.write("</svg>")


if __name__ == '__main__':
	file_to_svg(FILE_INPUT)