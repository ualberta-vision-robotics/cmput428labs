import os
import numpy as np
import trimesh
import pyrender
import cv2
import imageio
import time
from datetime import datetime

# Create images directory if it doesn't exist
os.makedirs('data/images', exist_ok=True)


# ---------------------------
# Load and Reorient the Mesh
# ---------------------------
obj_file = 'data/3d_models/zebra/zebra.obj'
mesh = trimesh.load(obj_file, process=False)

R_x = trimesh.transformations.rotation_matrix(np.radians(0), [1, 0, 0])
R_y = trimesh.transformations.rotation_matrix(np.radians(90), [0, 1, 0])
mesh.apply_transform(R_y @ R_x)

if hasattr(mesh.visual, 'material'):
    print("Loaded material:", mesh.visual.material.name)
    if hasattr(mesh.visual.material, 'image') and mesh.visual.material.image is not None:
        texture = mesh.visual.material.image
        print("Texture image size:", texture.size)
        texture_array = np.array(texture)
        print("Texture image shape:", texture_array.shape)
else:
    print("No material information found in the mesh.")

pyrender_mesh = pyrender.Mesh.from_trimesh(mesh)

# ---------------------------
# Create the Scene with Ambient Lighting
# ---------------------------
scene = pyrender.Scene(ambient_light=[1.5, 1.5, 1.5],
                         bg_color=[1.0, 1.0, 1.0])
scene.add(pyrender_mesh)

# ---------------------------
# Define the "look-at" Function (using world up = [0,1,0])
# ---------------------------
def compute_camera_pose(camera_position, target, up=np.array([0, 1, 0])):
    z_axis = camera_position - target
    z_axis = z_axis / np.linalg.norm(z_axis)
    
    # Ensure the chosen up vector is not parallel to z_axis.
    if np.allclose(np.abs(np.dot(up, z_axis)), 1.0, atol=1e-6):
        up = np.array([1, 0, 0])
    
    x_axis = np.cross(up, z_axis)
    norm_x = np.linalg.norm(x_axis)
    if norm_x < 1e-6:
        up = np.array([0, 0, 1])
        x_axis = np.cross(up, z_axis)
        norm_x = np.linalg.norm(x_axis)
    x_axis = x_axis / norm_x
    
    y_axis = np.cross(z_axis, x_axis)
    
    pose = np.eye(4)
    pose[:3, 0] = x_axis
    pose[:3, 1] = y_axis
    pose[:3, 2] = z_axis
    pose[:3, 3] = camera_position
    return pose

# ---------------------------
# Set Up Renderer and Camera Parameters
# ---------------------------
viewport_width = 640
viewport_height = 480
renderer = pyrender.OffscreenRenderer(viewport_width=viewport_width, viewport_height=viewport_height)
target = np.array([0, 0, 0])  # assume object is centered

# Use spherical coordinates where theta is the elevation measured from the horizontal.
# At theta = 0, the camera is in the horizontal plane.
r = 600.0        # distance from target
theta = 0.0      # elevation angle in radians (0 is horizontal)
phi = 0.0        # azimuth angle (rotation around the vertical axis)
epsilon = 0.01   # small epsilon to avoid degenerate cases

# Sinusoidal motion parameters for SfM recording
max_theta_oscillation = 0.01  # Maximum change in theta (elevation) in radians
max_phi_oscillation = 0.01   # Maximum change in phi (azimuth) in radians

camera_type = "perspective"  # start with perspective
snapshot_counter = 0
is_recording = False
video_writer = None
recording_frames = []
fps = 30
record_duration = 2  # seconds

print("Interactive Controls:")
print("  a/d: rotate left/right (phi)")
print("  w/s: raise/lower camera (theta)")
print("  q/e: zoom in/out")
print("  c: toggle camera type")
print("  space: capture a short video")
print("  ESC: exit")

# ---------------------------
# Main Loop: Render and Control the Camera
# ---------------------------
while True:
    # Compute camera position using spherical coordinates:
    # Here, theta is elevation from horizontal (increases upward)
    cam_x = r * np.cos(theta) * np.cos(phi)
    cam_z = r * np.cos(theta) * np.sin(phi)
    cam_y = r * np.sin(theta)
    camera_position = np.array([cam_x, cam_y, cam_z])
    
    # Compute camera pose using the up vector [0,1,0].
    cam_pose = compute_camera_pose(camera_position, target, up=np.array([0, 1, 0]))
    
    # Create camera based on current type.
    if camera_type == "perspective":
        camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    else:
        # Dynamically adjust orthographic parameters relative to distance.
        xmag = r / 2.0
        ymag = r / 2.0
        camera = pyrender.OrthographicCamera(xmag=xmag, ymag=ymag, znear=0.1, zfar=r*2)
    
    cam_node = scene.add(camera, pose=cam_pose)
    color, _ = renderer.render(scene)
    scene.remove_node(cam_node)
    
    # If we're recording, add the frame to our collection and update camera position
    if is_recording:
        recording_frames.append(color.copy())
        
        # Calculate current frame's progress through the total recording (0.0 to 1.0)
        progress = len(recording_frames) / (fps * record_duration)
        
        # Store the initial viewpoint for reference
        start_phi = phi
        start_theta = theta
        
        # Apply sinusoidal motion in both theta and phi
        # This creates smooth oscillation in both elevation and azimuth
        phi = start_phi + max_phi_oscillation * np.sin(progress * np.pi/2)
        theta = start_theta + max_theta_oscillation * np.sin(progress * 4 * np.pi)
        
        # Check if we've recorded enough frames
        if len(recording_frames) >= fps * record_duration:
            is_recording = False
            # Generate a timestamp-based filename to avoid overwriting
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"data/images/sfm_video_{timestamp}.mp4"
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                video_filename, 
                fourcc, 
                fps, 
                (viewport_width, viewport_height)
            )
            
            # Write all frames to video
            for frame in recording_frames:
                video_writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            video_writer.release()
            recording_frames = []
            print(f"Saved SfM video as {video_filename}")
            
            # Reset to original viewpoint
            phi = start_phi
            theta = start_theta
    
    # Display recording indicator if recording
    display_frame = color.copy()
    if is_recording:
        # Add a red recording indicator
        cv2.circle(display_frame, (30, 30), 15, (255, 0, 0), -1)
        cv2.putText(display_frame, f"Recording SfM: {len(recording_frames)}/{fps * record_duration} frames", 
                   (60, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    cv2.imshow("3D Viewer", cv2.cvtColor(display_frame, cv2.COLOR_RGB2BGR))
    
    key = cv2.waitKey(50) & 0xFF
    if key == 27:  # ESC to exit
        break
    elif key == ord('a'):  # Rotate left
        phi -= 0.1
    elif key == ord('d'):  # Rotate right
        phi += 0.1
    elif key == ord('w'):  # Raise camera: increase theta
        theta += 0.1
    elif key == ord('s'):  # Lower camera: decrease theta
        theta -= 0.1
    elif key == ord('q'):  # Zoom in
        r -= 10
        if r < 10:
            r = 10
    elif key == ord('e'):  # Zoom out
        r += 10
    elif key == ord('c'):  # Toggle camera type
        camera_type = "orthographic" if camera_type == "perspective" else "perspective"
        print("Camera type toggled to:", camera_type)
    elif key == 32 and not is_recording:  # Space bar: start recording video
        is_recording = True
        recording_frames = []
        print("Recording SfM video with sinusoidal motion...")

cv2.destroyAllWindows()
renderer.delete()