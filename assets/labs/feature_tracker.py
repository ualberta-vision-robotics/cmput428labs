import cv2
import numpy as np
import sys
from scipy.optimize import least_squares
import scipy.io as sio

def load_video_frames(video_path):
    """
    Load all frames from the video and convert them to grayscale.
    """
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Convert frame to grayscale.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frames.append(gray)
    cap.release()
    return frames

def detect_features(frame, max_corners=200, quality_level=0.01, min_distance=10):
    """
    Detect features (corners) in the first frame using goodFeaturesToTrack.
    """
    corners = cv2.goodFeaturesToTrack(frame,
                                      maxCorners=max_corners,
                                      qualityLevel=quality_level,
                                      minDistance=min_distance)
    if corners is not None:
        # corners is returned as (N,1,2); squeeze to (N,2)
        return np.squeeze(corners)
    else:
        return np.array([])

def detect_new_features(frame, existing_features, max_corners=50, quality_level=0.01, min_distance=10, mask_radius=10):
    """
    Detect new features in a frame, avoiding regions where features already exist.
    
    Parameters:
    frame (numpy.ndarray): Grayscale frame
    existing_features (list): List of (x,y) feature points that already exist
    max_corners, quality_level, min_distance: Parameters for goodFeaturesToTrack
    mask_radius (int): Radius around existing features to mask out
    
    Returns:
    numpy.ndarray: New detected features
    """
    # Create a mask to avoid detecting features near existing ones
    h, w = frame.shape
    mask = np.ones((h, w), dtype=np.uint8) * 255
    
    # Zero out regions around existing features
    for feat in existing_features:
        if feat is not None:
            x, y = int(round(feat[0])), int(round(feat[1]))
            cv2.circle(mask, (x, y), mask_radius, 0, -1)
    
    # Detect new features
    corners = cv2.goodFeaturesToTrack(frame,
                                      maxCorners=max_corners,
                                      qualityLevel=quality_level,
                                      minDistance=min_distance,
                                      mask=mask)
    if corners is not None:
        return np.squeeze(corners)
    else:
        return np.array([])

def track_features_with_redetection(frames, initial_features, redetect_interval=10, max_redetect=30):
    """
    Track features with periodic re-detection of new features.
    If features are lost, they remain None in the track. This allows the SfM algorithm
    to handle missing data later.
    
    Parameters:
    frames (list): List of grayscale frames
    initial_features (numpy.ndarray): Initial features to track
    redetect_interval (int): How often to detect new features (in frames)
    max_redetect (int): Maximum number of new features to detect at each interval
    
    Returns:
    dict: Dictionary of feature tracks mapping feature index to positions per frame
    """
    num_frames = len(frames)
    tracks = {i: [] for i in range(len(initial_features))}
    
    # Set initial positions for each feature in frame 0
    for i, pt in enumerate(initial_features):
        tracks[i].append(tuple(pt))
    
    # Initialize tracking
    prev_frame = frames[0]
    prev_pts = initial_features.astype(np.float32).reshape(-1, 1, 2)
    
    # Create active feature mask (1 if feature is being tracked, 0 if lost)
    active_features = np.ones(len(initial_features), dtype=bool)
    
    # Loop over frames to track features
    for i in range(1, num_frames):
        curr_frame = frames[i]
        
        # Only track active features
        if np.sum(active_features) > 0:
            active_prev_pts = prev_pts[active_features].reshape(-1, 1, 2)
            
            # Calculate optical flow for active features
            next_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_frame, curr_frame, active_prev_pts, None)
            
            # Update position of each feature
            idx_counter = 0
            for j, is_active in enumerate(active_features):
                if is_active:
                    if status[idx_counter][0] == 1:
                        tracks[j].append(tuple(next_pts[idx_counter][0]))
                        prev_pts[j] = next_pts[idx_counter]
                    else:
                        tracks[j].append(None)
                        active_features[j] = False
                    idx_counter += 1
                else:
                    tracks[j].append(None)
        else:
            # All features lost, append None to each track
            for j in range(len(initial_features)):
                tracks[j].append(None)
        
        # Periodically detect new features
        if i % redetect_interval == 0:
            # Get all current active features
            current_features = []
            for j, is_active in enumerate(active_features):
                if is_active:
                    current_features.append(prev_pts[j][0])
            
            # Detect new features
            new_features = detect_new_features(curr_frame, current_features, 
                                             max_corners=max_redetect, 
                                             quality_level=0.01, 
                                             min_distance=10)
            
            if len(new_features) > 0:
                if len(new_features.shape) == 1:
                    new_features = np.array([new_features])
                
                # Add new features to tracking
                for new_feat in new_features:
                    new_idx = len(tracks)
                    tracks[new_idx] = [None] * i  # Fill with None for previous frames
                    tracks[new_idx].append(tuple(new_feat))
                    
                    # Add to prev_pts for next iteration
                    prev_pts = np.vstack((prev_pts, new_feat.reshape(1, 1, 2)))
                    active_features = np.append(active_features, True)
        
        prev_frame = curr_frame
    
    return tracks

def track_features(frames, initial_features):
    """
    Track features using optical flow (calcOpticalFlowPyrLK) across all frames.
    Returns a dictionary mapping feature index to a list of (x,y) positions per frame.
    If tracking fails in a frame, None is stored.
    """
    num_frames = len(frames)
    tracks = {i: [] for i in range(len(initial_features))}
    
    # Set initial positions for each feature in frame 0.
    for i, pt in enumerate(initial_features):
        tracks[i].append(tuple(pt))
    
    prev_frame = frames[0]
    prev_pts = initial_features.astype(np.float32).reshape(-1, 1, 2)
    
    # Loop over frames to track features.
    for i in range(1, num_frames):
        curr_frame = frames[i]
        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_frame, curr_frame, prev_pts, None)
        for idx, (st, pt) in enumerate(zip(status, next_pts)):
            if st[0] == 1:
                tracks[idx].append(tuple(pt[0]))
            else:
                tracks[idx].append(None)  # Feature lost in this frame.
        prev_frame = curr_frame
        prev_pts = next_pts
    return tracks

def get_patch(image, center, patch_size):
    """
    Extract a patch of size (patch_size x patch_size) from image centered at 'center'.
    getRectSubPix performs bilinear interpolation to allow sub-pixel accuracy.
    """
    center_tuple = tuple(center)
    
    # Check if the center is within the image boundaries
    h, w = image.shape
    x, y = center
    if x < 0 or x >= w or y < 0 or y >= h:
        return np.zeros((patch_size, patch_size), dtype=image.dtype)
    
    patch = cv2.getRectSubPix(image, (patch_size, patch_size), center_tuple)
    return patch

def refine_track(track, frames, patch_size=15):
    """
    Given a feature track (list of (x,y) for each frame) and the video frames,
    refine the sub-pixel positions by minimizing the difference between a template patch
    (from the first frame) and the patches extracted at candidate positions in subsequent frames.
    
    The optimization is done globally across all frames (except the first, which is fixed).
    
    Returns the refined track, preserving None values for frames where tracking failed.
    """
    # Count valid positions (non-None)
    valid_positions = [i for i, pos in enumerate(track) if pos is not None]
    
    if len(valid_positions) <= 1:
        return track  # Not enough valid positions for refinement
    
    # Get first valid position to use as template
    first_valid_idx = valid_positions[0]
    template_pos = track[first_valid_idx]
    template_frame = frames[first_valid_idx]
    
    # Extract template patch
    template = get_patch(template_frame, template_pos, patch_size).astype(np.float32)
    
    # Prepare initial guess for optimization (all valid positions except the template)
    valid_positions_to_refine = valid_positions[1:]
    initial_positions = [track[i] for i in valid_positions_to_refine]
    initial_guess = np.array(initial_positions).flatten()
    
    def residuals(params):
        """
        Compute residuals between template and patches at candidate positions
        """
        pts = params.reshape(-1, 2)
        res = []
        
        for i, frame_idx in enumerate(valid_positions_to_refine):
            pt = pts[i]
            patch = get_patch(frames[frame_idx], pt, patch_size).astype(np.float32)
            diff = (patch - template).flatten()
            res.append(diff)
            
        return np.concatenate(res)
    
    # Run optimization
    try:
        result = least_squares(residuals, initial_guess, verbose=0, ftol=1e-5, xtol=1e-5)
        refined_positions = result.x.reshape(-1, 2)
        
        # Create refined track with original None values preserved
        refined_track = list(track)  # Make a copy
        for i, frame_idx in enumerate(valid_positions_to_refine):
            refined_track[frame_idx] = tuple(refined_positions[i])
            
        return refined_track
    except Exception as e:
        print(f"Refinement failed: {e}")
        return track  # Return original track if refinement fails

def visualize_tracks(frames, refined_tracks, output_path='tracked_output.avi', fps=30):
    """
    Visualize the refined tracks by overlaying them on the video frames.
    This function writes the visualization to an output video file.
    """
    # Convert grayscale frames to BGR color frames for visualization.
    color_frames = [cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR) for frame in frames]
    
    # Create random colors for each feature track.
    colors = {}
    for feature_index in refined_tracks.keys():
        colors[feature_index] = (int(np.random.randint(0, 255)),
                                 int(np.random.randint(0, 255)),
                                 int(np.random.randint(0, 255)))
    
    num_frames = len(frames)
    # Draw the tracks on each frame.
    for i in range(num_frames):
        for feature_index, track in refined_tracks.items():
            if i < len(track) and track[i] is not None:
                x, y = track[i]
                # Draw a small circle for the current feature point.
                cv2.circle(color_frames[i], (int(round(x)), int(round(y))), 3, colors[feature_index], -1)
                # Draw line connecting previous point (if available).
                if i > 0 and i-1 < len(track) and track[i-1] is not None:
                    prev_x, prev_y = track[i-1]
                    cv2.circle(color_frames[i], (int(round(prev_x)), int(round(prev_y))), 1, colors[feature_index], -1)
                    cv2.line(color_frames[i], (int(round(prev_x)), int(round(prev_y))),
                             (int(round(x)), int(round(y))), colors[feature_index], 1)
    
    # Set up the video writer.
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    
    for frame in color_frames:
        out.write(frame)
    out.release()
    print(f"Visualization saved to {output_path}")

def save_tracks_to_mat(refined_tracks, num_frames, filename='tracks.mat'):
    """
    Save the refined tracks in a MATLAB .mat file with separate keys for x and y coordinates.
    Handles tracks of different lengths and missing values with NaN.
    
    Parameters:
    refined_tracks (dict): Dictionary of feature tracks
    num_frames (int): Total number of frames in the video
    filename (str): Output filename
    """
    # Sort track keys to ensure consistent order
    sorted_track_ids = sorted(refined_tracks.keys())
    
    # Initialize arrays to store x and y coordinates
    n_features = len(sorted_track_ids)
    track_x = np.full((n_features, num_frames), np.nan)
    track_y = np.full((n_features, num_frames), np.nan)
    
    # Fill in the arrays with tracked coordinates
    for i, track_id in enumerate(sorted_track_ids):
        track = refined_tracks[track_id]
        for j, pos in enumerate(track):
            if j < num_frames and pos is not None:
                track_x[i, j] = pos[0]
                track_y[i, j] = pos[1]
    
    # Save to .mat file
    sio.savemat(filename, {'track_x': track_x, 'track_y': track_y})
    print(f"Tracks data saved to {filename}")
    
    # Print tracking statistics
    total_points = n_features * num_frames
    tracked_points = np.sum(~np.isnan(track_x))
    percent_tracked = 100 * tracked_points / total_points
    
    print(f"Tracking Statistics:")
    print(f"  Total features: {n_features}")
    print(f"  Total frames: {num_frames}")
    print(f"  Points tracked: {tracked_points}/{total_points} ({percent_tracked:.2f}%)")
    
    # Calculate feature coverage per frame
    coverage_per_frame = np.sum(~np.isnan(track_x), axis=0) / n_features * 100
    print(f"  Min frame coverage: {np.min(coverage_per_frame):.2f}%")
    print(f"  Max frame coverage: {np.max(coverage_per_frame):.2f}%")
    print(f"  Mean frame coverage: {np.mean(coverage_per_frame):.2f}%")

def main(video_path):
    # Load video frames (grayscale).
    frames = load_video_frames(video_path)
    if not frames:
        print("No frames loaded. Please check the video path.")
        return
    print(f"Loaded {len(frames)} frames.")
    
    # Detect features in the first frame.
    features = detect_features(frames[0])
    if features.size == 0:
        print("No features detected.")
        return
    print(f"Detected {len(features)} features in the first frame.")
    
    # Track features across frames using optical flow with re-detection.
    tracks = track_features_with_redetection(frames, features, redetect_interval=15, max_redetect=20)
    print("Initial tracking complete.")
    
    # Refine each feature track using global optimization for sub-pixel accuracy.
    refined_tracks = {}
    for i, track in tracks.items():
        refined = refine_track(track, frames, patch_size=15)
        refined_tracks[i] = refined
        
        # Print summary info for the track
        valid_positions = [pos for pos in refined if pos is not None]
        print(f"Refined track {i}: {len(valid_positions)}/{len(frames)} frames tracked")
    
    # Visualize the refined tracks by overlaying them on the frames.
    visualize_tracks(frames, refined_tracks, output_path='tracked_output.avi', fps=30)
    
    # Save the refined tracks in a .mat file.
    save_tracks_to_mat(refined_tracks, len(frames), filename='tracks.mat')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python feature_tracker.py <video_path>")
    else:
        main(sys.argv[1])