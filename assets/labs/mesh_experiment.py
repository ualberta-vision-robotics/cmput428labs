import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import trimesh
import os
from scipy.spatial import KDTree
import urllib.request

prefix = "max-planck"

class MeshOrthographicSFM:
    """
    Implementation of Structure from Motion using orthographic projection with a 3D mesh.
    Properly handles occlusions by determining which vertices are visible from the camera.
    """
    def __init__(self, mesh_path=None, n_frames=226, rotation_per_frame=2, 
                 max_features=None, z_buffer_resolution=512):
        """
        Initialize the MeshOrthographicSFM system.
        
        Parameters:
        - mesh_path: Path to the mesh file (OBJ, STL, etc.)
        - n_frames: Total number of frames
        - rotation_per_frame: Rotation angle in degrees per frame
        - max_features: Maximum number of features to track (None for all vertices)
        - z_buffer_resolution: Resolution of the z-buffer for occlusion detection
        """
        self.n_frames = n_frames
        self.rotation_per_frame = rotation_per_frame
        self.max_features = max_features
        self.z_buffer_resolution = z_buffer_resolution
        
        # Load mesh (or download Stanford bunny if no mesh provided)
        if mesh_path is None:
            mesh_path = self._download_stanford_bunny()
            
        self.mesh = self._load_mesh(mesh_path)
        print(f"Loaded mesh with {len(self.mesh.vertices)} vertices and {len(self.mesh.faces)} faces")
        
        # Center and normalize the mesh
        self.mesh = self._normalize_mesh(self.mesh)
        
        # Initialize tracking data structures
        self.feature_tracks = []  # Will store the track of each feature
        self.next_feature_id = 0  # Counter for assigning new feature IDs
        self.vertex_to_feature_id = {}  # Maps vertex index to feature ID
        
        # Initialize matrices
        self.W = None  # Measurement matrix
        self.fill_matrix = None  # Fill matrix
        
    def _download_stanford_bunny(self):
        """Download Stanford bunny if not already present."""
        bunny_url = "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/stanford-bunny.obj"
        # local_path = "bunny_low_poly.obj"
        local_path = f"data/mesh/{prefix}.obj"
        
        if not os.path.exists(local_path):
            print(f"Downloading Stanford bunny mesh from {bunny_url}")
            urllib.request.urlretrieve(bunny_url, local_path)
        else:
            print("Using existing Stanford bunny mesh")
            
        return local_path
        
    def _load_mesh(self, mesh_path):
        """
        Load a mesh from a file.
        
        Parameters:
        - mesh_path: Path to the mesh file
        
        Returns:
        - trimesh.Trimesh object
        """
        try:
            mesh = trimesh.load(mesh_path)
            return mesh
        except Exception as e:
            print(f"Error loading mesh: {e}")
            # If loading fails, create a simple cube mesh
            print("Creating a simple cube mesh instead")
            return trimesh.creation.box()
            
    def _normalize_mesh(self, mesh):
        """
        Center the mesh at the origin and scale to fit in a unit sphere.
        
        Parameters:
        - mesh: trimesh.Trimesh object
        
        Returns:
        - Normalized mesh
        """
        # Get the center of mass
        center = mesh.centroid
        
        # Translate to center
        mesh.vertices -= center
        
        # Scale to fit in a unit sphere
        max_radius = np.max(np.linalg.norm(mesh.vertices, axis=1))
        mesh.vertices /= max_radius
        
        return mesh
        
    def _rotation_matrix_y(self, angle_deg):
        """
        Create a rotation matrix for rotation around the y-axis.
        
        Parameters:
        - angle_deg: Rotation angle in degrees
        
        Returns:
        - 3x3 rotation matrix
        """
        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        # Rotation matrix around y-axis
        R = np.array([
            [cos_a, 0, sin_a],
            [0, 1, 0],
            [-sin_a, 0, cos_a]
        ])
        
        return R
        
    def _determine_visible_vertices(self, rotated_vertices, rotated_faces):
        """
        Determine which vertices are visible from an orthographic camera looking along the z-axis.
        Uses a simplified and more efficient approach for orthographic projection.
        
        Parameters:
        - rotated_vertices: Vertices after rotation
        - rotated_faces: Faces after rotation
        
        Returns:
        - Mask of visible vertices
        - Depth values for visible vertices
        """
        print("  Determining visible vertices...")
        n_vertices = len(rotated_vertices)
        
        # Step 1: Perform backface culling to eliminate faces that point away from camera
        print("  Performing backface culling...")
        face_visible = np.zeros(len(rotated_faces), dtype=bool)
        
        for face_idx, face in enumerate(rotated_faces):
            # Get vertices of the face
            v = rotated_vertices[face]
            
            # Calculate face normal using cross product of edges
            normal = np.cross(v[1] - v[0], v[2] - v[0])
            
            # If z-component of normal is negative, face is visible to camera
            face_visible[face_idx] = normal[2] < 0
        
        # Step 2: Find visible vertices using a simpler approach for orthographic projection
        # Initialize with all vertices not visible
        visible_mask = np.zeros(n_vertices, dtype=bool)
        depth_values = np.full(n_vertices, np.inf)
        
        # 2D grid for visibility (much coarser than before for speed)
        resolution = min(100, self.z_buffer_resolution)  # Lower resolution for better performance
        
        # Get bounds of vertices
        x_min, y_min = np.min(rotated_vertices[:, :2], axis=0) - 0.01
        x_max, y_max = np.max(rotated_vertices[:, :2], axis=0) + 0.01
        
        # Create grid cells
        x_edges = np.linspace(x_min, x_max, resolution + 1)
        y_edges = np.linspace(y_min, y_max, resolution + 1)
        
        # Create 2D grid for z-buffer
        z_buffer = {}  # (cell_x, cell_y) -> (vertex_idx, z_value)
        
        # Find which cell each vertex belongs to
        print("  Processing vertices...")
        for i, vertex in enumerate(rotated_vertices):
            x, y, z = vertex
            
            # Find grid cell
            cell_x = min(resolution - 1, max(0, np.searchsorted(x_edges, x) - 1))
            cell_y = min(resolution - 1, max(0, np.searchsorted(y_edges, y) - 1))
            cell = (cell_x, cell_y)
            
            # Check if this vertex is closer than the current one in the cell
            if cell not in z_buffer or z < z_buffer[cell][1]:
                z_buffer[cell] = (i, z)
        
        print("  Finalizing visible vertices...")
        # Vertices from z-buffer are visible
        for (i, z) in z_buffer.values():
            visible_mask[i] = True
            depth_values[i] = z
        
        # Further refine by keeping only vertices that are part of at least one visible face
        # This gives more accurate results
        vertices_in_visible_faces = set()
        for face_idx, face in enumerate(rotated_faces):
            if face_visible[face_idx]:
                vertices_in_visible_faces.update(face)
        
        # Final mask: vertex is visible only if in z-buffer AND part of a visible face
        for i in range(n_vertices):
            visible_mask[i] = visible_mask[i] and (i in vertices_in_visible_faces)
        
        return visible_mask, depth_values
    
    def _point_in_triangle_2d(self, p, v1, v2, v3):
        """
        Check if a 2D point is inside a triangle using barycentric coordinates.
        
        Parameters:
        - p: Point to check
        - v1, v2, v3: Vertices of the triangle
        
        Returns:
        - inside: Boolean indicating if point is inside triangle
        - barycentric: Barycentric coordinates of the point
        """
        # Convert to barycentric coordinates
        area = 0.5 * np.abs(np.cross(v2 - v1, v3 - v1))
        if area < 1e-10:  # Triangle has zero area
            return False, None
            
        area1 = 0.5 * np.abs(np.cross(v2 - p, v3 - p))
        area2 = 0.5 * np.abs(np.cross(v3 - p, v1 - p))
        area3 = 0.5 * np.abs(np.cross(v1 - p, v2 - p))
        
        # Calculate barycentric coordinates
        s = area1 / area
        t = area2 / area
        u = area3 / area
        
        # Check if point is inside triangle (allowing for small numerical errors)
        eps = 1e-5
        inside = (s >= -eps) and (t >= -eps) and (u >= -eps) and (s + t + u <= 1 + eps)
        
        return inside, np.array([s, t, u])
            
    def process(self):
        """
        Process the entire sequence, building the measurement matrix and fill matrix.
        """
        print("Initializing tracking structures...")
        # Initialize tracking structures
        self.feature_tracks = []
        self.next_feature_id = 0
        self.vertex_to_feature_id = {}
        
        # Set of visible feature IDs for each frame
        active_features_by_frame = []
        
        # Get mesh data
        vertices = self.mesh.vertices
        faces = self.mesh.faces
        
        # Limit number of vertices if requested
        n_vertices = len(vertices)
        vertex_indices = np.arange(n_vertices)
        
        if self.max_features is not None and self.max_features < n_vertices:
            # Randomly sample vertices
            np.random.seed(42)
            vertex_indices = np.random.choice(n_vertices, self.max_features, replace=False)
            print(f"Using {self.max_features} vertices out of {n_vertices} total")
        
        print("Processing first frame...")
        # Process first frame specially to number vertices from left to right
        frame_idx = 0
        total_rotation = 0
        
        # Compute rotation matrix for first frame
        R = self._rotation_matrix_y(total_rotation)
        
        # Rotate all vertices and faces
        rotated_vertices = np.dot(vertices, R)
        
        # Determine which vertices are visible
        visible_mask, depth_values = self._determine_visible_vertices(rotated_vertices, faces)
        
        # Filter to vertices we're tracking
        vertex_mask = np.zeros(n_vertices, dtype=bool)
        vertex_mask[vertex_indices] = True
        visible_mask = visible_mask & vertex_mask
        
        # Get indices of visible vertices
        visible_indices = np.where(visible_mask)[0]
        
        print(f"  Found {len(visible_indices)} visible vertices in first frame")
        
        # Get 2D projections of visible vertices (x,y coordinates)
        visible_points_2d = rotated_vertices[visible_mask, :2]
        
        # Sort visible vertices by x-coordinate (left to right)
        sorted_indices = np.argsort(visible_points_2d[:, 0])
        
        # List to store feature IDs visible in this frame
        visible_feature_ids = []
        
        # Assign IDs to vertices from left to right
        for i, sort_idx in enumerate(sorted_indices):
            vertex_idx = visible_indices[sort_idx]
            
            # Assign new feature ID
            self.vertex_to_feature_id[vertex_idx] = self.next_feature_id
            self.feature_tracks.append([])
            visible_feature_ids.append(self.next_feature_id)
            
            # Get 2D projection of this vertex
            point_2d = visible_points_2d[sort_idx]
            
            # Store the projection in the feature track
            self.feature_tracks[self.next_feature_id].append((frame_idx, point_2d))
            
            # Increment feature ID
            self.next_feature_id += 1
        
        # Store visible feature IDs for first frame
        active_features_by_frame.append(visible_feature_ids)
        
        # Update total rotation for next frame
        total_rotation += self.rotation_per_frame
        
        print("Processing remaining frames...")
        # Process remaining frames
        for frame_idx in range(1, self.n_frames):
            print(f"Processing frame {frame_idx}/{self.n_frames}...")
            
            # Compute rotation matrix for current total rotation
            R = self._rotation_matrix_y(total_rotation)
            
            # Rotate all vertices
            rotated_vertices = np.dot(vertices, R)
            
            # Determine which vertices are visible
            visible_mask, depth_values = self._determine_visible_vertices(rotated_vertices, faces)
            
            # Filter to vertices we're tracking
            visible_mask = visible_mask & vertex_mask
            
            # Get indices of visible vertices
            visible_indices = np.where(visible_mask)[0]
            
            print(f"  Found {len(visible_indices)} visible vertices")
            
            # List to store feature IDs visible in this frame
            visible_feature_ids = []
            
            # Process each visible vertex
            for vertex_idx in visible_indices:
                # If this vertex doesn't have a feature ID yet, assign a new one
                if vertex_idx not in self.vertex_to_feature_id:
                    self.vertex_to_feature_id[vertex_idx] = self.next_feature_id
                    self.feature_tracks.append([])
                    self.next_feature_id += 1
                
                # Get feature ID for this vertex
                feature_id = self.vertex_to_feature_id[vertex_idx]
                visible_feature_ids.append(feature_id)
                
                # Get 2D projection of this vertex
                point_2d = rotated_vertices[vertex_idx, :2]
                
                # Store the projection in the feature track
                self.feature_tracks[feature_id].append((frame_idx, point_2d))
            
            # Store visible feature IDs for this frame
            active_features_by_frame.append(visible_feature_ids)
            
            # Update total rotation for next frame
            total_rotation += self.rotation_per_frame
        
        print("Building matrices...")
        # Now build the W matrix and fill matrix from the tracked features
        self._build_matrices(active_features_by_frame)
        
    def _build_matrices(self, active_features_by_frame):
        """
        Build the measurement matrix W and fill matrix.
        
        Parameters:
        - active_features_by_frame: List of visible feature IDs for each frame
        """
        # Get the total number of features
        total_features = self.next_feature_id
        
        # Initialize the fill matrix
        self.fill_matrix = np.zeros((self.n_frames, total_features), dtype=np.uint8)
        
        # Initialize the measurement matrices
        W_x = np.zeros((self.n_frames, total_features))
        W_y = np.zeros((self.n_frames, total_features))
        
        # Fill in the matrices based on feature tracks
        for feat_id, track in enumerate(self.feature_tracks):
            for frame_idx, point_2d in track:
                # Update fill matrix to show this point is visible
                self.fill_matrix[frame_idx, feat_id] = 1
                
                # Store x,y coordinates in measurement matrices
                W_x[frame_idx, feat_id] = point_2d[0]
                W_y[frame_idx, feat_id] = point_2d[1]
        
        # Create the combined measurement matrix W = [W_x; W_y]
        self.W = np.vstack((W_x, W_y))
        
        # Store individual coordinate matrices for convenience
        self.W_x = W_x
        self.W_y = W_y
        
    def save_matrices(self):
        """
        Save the measurement matrix and fill matrix as NPY files.
        
        Parameters:
        - prefix: Prefix for the output filenames
        
        Returns:
        - List of saved filenames
        """
        # Ensure matrices are built
        if self.W is None or self.fill_matrix is None:
            print("Matrices not available. Run process() first.")
            return []
            
        # Create output filenames
        w_filename = f"data/ortho/{prefix}_measurement_matrix.npy"
        w_x_filename = f"data/ortho/{prefix}_measurement_matrix_x.npy"
        w_y_filename = f"data/ortho/{prefix}_measurement_matrix_y.npy"
        fill_filename = f"data/ortho/{prefix}_fill_matrix.npy"
        
        # Save matrices
        np.save(w_filename, self.W)
        np.save(w_x_filename, self.W_x)
        np.save(w_y_filename, self.W_y)
        np.save(fill_filename, self.fill_matrix)
        
        # Return list of saved files
        saved_files = [w_filename, w_x_filename, w_y_filename, fill_filename]
        print(f"Saved matrices to: {', '.join(saved_files)}")
        
        return saved_files
        
    def prepare_for_factorization(self, fill_missing=True, center_data=True):
        """
        Prepare the measurement matrix for factorization by handling missing data
        and centering the coordinates.
        
        Parameters:
        - fill_missing: Whether to fill missing entries (True) or use only complete columns/rows
        - center_data: Whether to center the data by subtracting the mean of each row
        
        Returns:
        - W_prepared: Prepared measurement matrix
        - row_means: Mean of each row (if center_data=True)
        - valid_features: Indices of features used (if fill_missing=False)
        """
        # Ensure matrices are built
        if self.W is None or self.fill_matrix is None:
            print("Matrices not available. Run process() first.")
            return None, None, None
            
        # Make a copy to avoid modifying the original
        W_x = self.W_x.copy()
        W_y = self.W_y.copy()
        
        if fill_missing:
            # Strategy 1: Fill missing entries with the mean of the column
            # This is a simple approach; more sophisticated methods could be used
            
            # For each column (feature)
            for j in range(W_x.shape[1]):
                # Get valid entries for this feature
                valid_x = self.fill_matrix[:, j] == 1
                valid_y = self.fill_matrix[:, j] == 1  # Same as valid_x in our case
                
                if np.any(valid_x) and not np.all(valid_x):
                    # Compute mean of valid entries
                    mean_x = np.mean(W_x[valid_x, j])
                    mean_y = np.mean(W_y[valid_y, j])
                    
                    # Fill missing entries with mean
                    W_x[~valid_x, j] = mean_x
                    W_y[~valid_y, j] = mean_y
            
            valid_features = np.arange(W_x.shape[1])
        else:
            # Strategy 2: Use only features that are visible in all frames
            # This is more restrictive but avoids filling missing data
            
            # Find features visible in all frames
            complete_features = np.all(self.fill_matrix == 1, axis=0)
            valid_features = np.where(complete_features)[0]
            
            if len(valid_features) == 0:
                print("Warning: No features visible in all frames. Try using fill_missing=True.")
                return None, None, None
                
            # Select only complete columns
            W_x = W_x[:, valid_features]
            W_y = W_y[:, valid_features]
        
        # Center the data by subtracting the mean of each row
        row_means = None
        if center_data:
            # Compute mean of each row
            row_means_x = np.mean(W_x, axis=1, keepdims=True)
            row_means_y = np.mean(W_y, axis=1, keepdims=True)
            
            # Subtract mean
            W_x = W_x - row_means_x
            W_y = W_y - row_means_y
            
            # Store the means
            row_means = np.vstack((row_means_x, row_means_y))
        
        # Stack to form the prepared measurement matrix
        W_prepared = np.vstack((W_x, W_y))
        
        return W_prepared, row_means, valid_features
        
    def visualize_fill_matrix(self, show_details=True):
        """
        Visualize the fill matrix.
        
        Parameters:
        - show_details: Whether to print details about the fill matrix
        
        Returns:
        - Matplotlib figure
        """
        if self.fill_matrix is None:
            print("Fill matrix not available. Run process() first.")
            return None
            
        plt.figure(figsize=(10, 8))
        plt.imshow(self.fill_matrix, cmap='gray', aspect='auto')
        plt.title('Fill Matrix')
        plt.xlabel('Feature ID')
        plt.ylabel('Frame Number')
        plt.colorbar(label='Visibility')
        plt.tight_layout()
        
        if show_details:
            total_entries = self.fill_matrix.size
            known_entries = np.sum(self.fill_matrix)
            percentage = (known_entries / total_entries) * 100
            
            print(f"Fill matrix shape: {self.fill_matrix.shape}")
            print(f"Total entries: {total_entries}")
            print(f"Known entries: {known_entries}")
            print(f"Percentage known: {percentage:.2f}%")
        
        return plt.gcf()
        
    def visualize_tracks(self, n_tracks=60):
        """
        Visualize a random subset of feature tracks.
        
        Parameters:
        - n_tracks: Number of random tracks to visualize
        
        Returns:
        - Matplotlib figure
        """
        if not self.feature_tracks:
            print("Feature tracks not available. Run process() first.")
            return None
            
        # Total number of features
        total_features = len(self.feature_tracks)
        
        # Select random feature IDs
        if n_tracks >= total_features:
            n_tracks = total_features
            
        np.random.seed(42)  # For reproducibility
        selected_ids = np.random.choice(total_features, n_tracks, replace=False)
        
        plt.figure(figsize=(8, 8))
        
        # Loop through selected features
        for feat_id in selected_ids:
            # Get track for this feature
            track = self.feature_tracks[feat_id]
            
            # Skip if track is empty
            if not track or len(track) < 2:  # Need at least 2 points to draw a line
                continue
                
            # Extract frame indices and points
            frames, points = zip(*track)
            points = np.array(points)
            
            # Plot track
            plt.plot(points[:, 0], points[:, 1], '-', linewidth=0.5)
            
            # Mark start and end
            plt.plot(points[0, 0], points[0, 1], 'bo', markersize=3)
            plt.plot(points[-1, 0], points[-1, 1], 'ro', markersize=3)
        
        plt.title(f'{n_tracks} Feature Tracks')
        plt.axis('equal')
        plt.grid(True)
        plt.tight_layout()
        
        return plt.gcf()
        
    def visualize_mesh_tracking(self, frame_idx=0):
        """
        Visualize the mesh and tracked features at a specific frame.
        
        Parameters:
        - frame_idx: Frame index to visualize
        
        Returns:
        - Matplotlib figure
        """
        if not self.feature_tracks:
            print("Feature tracks not available. Run process() first.")
            return None
            
        # Set up the figure with two subplots: 3D mesh and 2D projection
        fig = plt.figure(figsize=(15, 7))
        ax1 = fig.add_subplot(121, projection='3d')
        ax2 = fig.add_subplot(122)
        
        # Compute rotation for the selected frame
        R = self._rotation_matrix_y(frame_idx * self.rotation_per_frame)
        
        # Rotate the mesh
        rotated_vertices = np.dot(self.mesh.vertices, R)
        
        # Determine visible vertices
        visible_mask, _ = self._determine_visible_vertices(rotated_vertices, self.mesh.faces)
        
        # 1. Plot the 3D mesh
        # Plot all vertices
        ax1.scatter(
            rotated_vertices[:, 0],
            rotated_vertices[:, 1],
            rotated_vertices[:, 2],
            c='lightgray', marker='.', alpha=0.3, s=5
        )
        
        # Highlight visible vertices
        ax1.scatter(
            rotated_vertices[visible_mask, 0],
            rotated_vertices[visible_mask, 1],
            rotated_vertices[visible_mask, 2],
            c='green', marker='o', alpha=0.7, s=10
        )
        
        # Plot tracked features for this frame
        visible_feature_ids = []
        visible_points = []
        
        for feat_id, track in enumerate(self.feature_tracks):
            for track_frame_idx, point in track:
                if track_frame_idx == frame_idx:
                    visible_feature_ids.append(feat_id)
                    visible_points.append(point)
                    break
        
        # If any tracked features are visible, plot them
        if visible_feature_ids:
            # Find the corresponding 3D vertices
            visible_feature_vertices = []
            for feat_id in visible_feature_ids:
                # Find the vertex index for this feature
                for vertex_idx, vertex_feat_id in self.vertex_to_feature_id.items():
                    if vertex_feat_id == feat_id:
                        visible_feature_vertices.append(rotated_vertices[vertex_idx])
                        break
            
            visible_feature_vertices = np.array(visible_feature_vertices)
            
            # Plot tracked features
            ax1.scatter(
                visible_feature_vertices[:, 0],
                visible_feature_vertices[:, 1],
                visible_feature_vertices[:, 2],
                c='red', marker='o', s=20
            )
                
        # Set axis labels and title
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_zlabel('Z')
        ax1.set_title('3D Mesh with Tracked Features')
        
        # Make axis limits equal to preserve the shape
        ax1.set_box_aspect([1, 1, 1])
        
        # Adjust the view to look along the z-axis (like the orthographic camera)
        ax1.view_init(elev=0, azim=-90)
        
        # 2. Plot the 2D orthographic projection
        visible_points = np.array(visible_points)
        
        # Plot projected points
        if len(visible_points) > 0:
            ax2.scatter(visible_points[:, 0], visible_points[:, 1], c=visible_feature_ids, cmap='viridis', s=20)
        
        # Set axis labels and title
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        ax2.set_title('Orthographic Projection with Tracked Features')
        ax2.axis('equal')
        ax2.grid(True)
        
        # Add colorbar
        if len(visible_points) > 0:
            cbar = plt.colorbar(ax2.collections[0], ax=ax2)
            cbar.set_label('Feature ID')
        
        # Add frame info
        fig.suptitle(f'Frame {frame_idx} (Rotation: {frame_idx * self.rotation_per_frame}°)')
        
        plt.tight_layout()
        
        return fig
        
    def create_tracking_visualization(self, output_path=f"data/ortho/{prefix}_mesh_tracking.mp4", dpi=100, frame_interval=1):
        """
        Create a video showing the orthographic projection of the mesh and the growing fill matrix.
        
        Parameters:
        - output_path: Path to save the video
        - dpi: Resolution of the video
        - frame_interval: Interval between frames to visualize (to reduce file size)
        """
        import matplotlib.animation as animation
        from matplotlib.collections import PolyCollection
        
        if not self.feature_tracks:
            print("Feature tracks not available. Run process() first.")
            return
            
        # Set up the figure with two subplots (2D projection and fill matrix)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Set up static elements
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_title('Orthographic Projection with Mesh')
        ax1.set_xlim(-1.5, 1.5)
        ax1.set_ylim(-1.5, 1.5)
        ax1.grid(True)
        
        ax2.set_xlabel('Feature ID')
        ax2.set_ylabel('Frame Number')
        ax2.set_title('Growing Fill Matrix')
        
        # Create frames list with interval
        frames = list(range(0, self.n_frames, frame_interval))
        if frames[-1] != self.n_frames - 1:
            frames.append(self.n_frames - 1)
        
        # Initialize color map for consistent feature coloring
        cmap = plt.cm.viridis
        
        # Initialize empty fill matrix for visualization
        fill_matrix_vis = np.zeros((self.n_frames, self.next_feature_id))
        
        # Create animation
        def update(frame_idx):
            ax1.clear()
            
            # Set up static elements again (they get cleared)
            ax1.set_xlabel('X')
            ax1.set_ylabel('Y')
            ax1.set_title('Orthographic Projection with Mesh')
            ax1.set_xlim(-1.5, 1.5)
            ax1.set_ylim(-1.5, 1.5)
            ax1.grid(True)
            
            # Compute rotation for the current frame
            R = self._rotation_matrix_y(frame_idx * self.rotation_per_frame)
            
            # Rotate the mesh
            rotated_vertices = np.dot(self.mesh.vertices, R)
            
            # Show the mesh in orthographic projection (just x and y coordinates)
            # We'll draw the faces of the mesh as polygons
            polys = []
            for face in self.mesh.faces:
                # Get vertices for this face
                face_verts = rotated_vertices[face, :2]  # Just take x, y for orthographic
                
                # Calculate face normal to determine if it's visible
                v0, v1, v2 = rotated_vertices[face]
                edge1 = v1 - v0
                edge2 = v2 - v0
                normal = np.cross(edge1, edge2)
                
                # Only add face if it's visible (normal points toward camera)
                if normal[2] < 0:
                    polys.append(face_verts)
            
            # Create a PolyCollection to display all faces efficiently
            colors = np.linspace(0.2, 0.8, len(polys))
            poly_collection = PolyCollection(
                polys,
                facecolors=['lightgray'],
                edgecolors=['gray'],
                linewidths=0.5,
                alpha=0.7
            )
            ax1.add_collection(poly_collection)
            
            # Plot tracked features for this frame
            visible_feature_ids = []
            visible_points = []
            
            for feat_id, track in enumerate(self.feature_tracks):
                for track_frame_idx, point in track:
                    if track_frame_idx == frame_idx:
                        visible_feature_ids.append(feat_id)
                        visible_points.append(point)
                        break
            
            # Convert to arrays
            visible_points = np.array(visible_points)
            visible_feature_ids = np.array(visible_feature_ids)
            
            # Plot projected points
            if len(visible_points) > 0:
                scatter = ax1.scatter(
                    visible_points[:, 0], 
                    visible_points[:, 1], 
                    c=visible_feature_ids, 
                    cmap=cmap, 
                    vmin=0, 
                    vmax=self.next_feature_id - 1,
                    s=30,
                    zorder=10  # Make sure points are on top of the mesh
                )
            
            # Update fill matrix for current frame
            for feat_id in visible_feature_ids:
                # Mark all frames up to current frame for this feature
                for f in range(frame_idx + 1):
                    # Check if this feature was visible in frame f
                    visible_in_f = any(
                        track_f == f for track_f, _ in self.feature_tracks[feat_id]
                    )
                    if visible_in_f:
                        fill_matrix_vis[f, feat_id] = 1
            
            # Plot the current fill matrix
            ax2.clear()
            ax2.set_xlabel('Feature ID')
            ax2.set_ylabel('Frame Number')
            ax2.set_title('Growing Fill Matrix')
            
            # Show fill matrix up to current frame
            current_fill = fill_matrix_vis[:frame_idx+1, :]
            if current_fill.size > 0:  # Only show if we have data
                img = ax2.imshow(
                    current_fill, 
                    cmap='Blues', 
                    aspect='auto',
                    origin='upper'
                )
                
                # Add colorbar if not already added
                if not hasattr(update, 'colorbar_added_fill'):
                    cbar = plt.colorbar(img, ax=ax2)
                    cbar.set_label('Visibility')
                    update.colorbar_added_fill = True
            
            # Add frame info
            fig.suptitle(f'Frame {frame_idx}/{self.n_frames-1} (Rotation: {frame_idx * self.rotation_per_frame}°)\n'
                        f'Visible features: {len(visible_feature_ids)} / Total features: {self.next_feature_id}')
            
            return []
        
        # Create animation
        ani = animation.FuncAnimation(fig, update, frames=frames, blit=False)
        
        # Save as MP4
        print(f"Creating video: {output_path}")
        ani.save(output_path, dpi=dpi, writer='ffmpeg')
        plt.close(fig)
        
        # Create animation
        ani = animation.FuncAnimation(fig, update, frames=frames, blit=True)
        
        # Save as MP4
        print(f"Creating video: {output_path}")
        ani.save(output_path, dpi=dpi, writer='ffmpeg')
        plt.close(fig)


def main():
    """Main function to demonstrate the mesh SFM."""
    # Create a MeshOrthographicSFM object
    # We'll use the Stanford bunny (downloaded automatically if not available)
    # Reduce parameters to make it run faster
    sfm = MeshOrthographicSFM(
        mesh_path=None,  # Uses Stanford bunny by default
        n_frames=60,     # Much fewer frames to reduce processing time
        rotation_per_frame=6,  # Larger rotation per frame
        max_features=20000,  # Limit number of features for better performance
        z_buffer_resolution=1000  # Lower resolution z-buffer for faster occlusion detection
    )
    
    # Process the data
    print("Processing data...")
    sfm.process()
    
    # Visualize the fill matrix
    print("Visualizing fill matrix...")
    fill_fig = sfm.visualize_fill_matrix()
    
    # Save the fill matrix figure
    fill_fig.savefig(f"data/ortho/{prefix}mesh_fill_matrix.png")
    print("Saved fill matrix visualization to 'mesh_fill_matrix.png'")
    
    # Visualize random tracks
    print("Visualizing random tracks...")
    tracks_fig = sfm.visualize_tracks(n_tracks=60)
    
    # Save the tracks figure
    # tracks_fig.savefig("mesh_feature_tracks.png")
    # print("Saved feature tracks visualization to 'mesh_feature_tracks.png'")
    
    # Create video visualization with frame_interval=2 to reduce file size
    print("Creating tracking visualization video...")
    sfm.create_tracking_visualization(frame_interval=2)
    print("Video visualization complete!")
    
    # Save the matrices for further analysis
    print("Saving matrices as NPY files...")
    sfm.save_matrices()
    
    # Prepare measurement matrix for factorization
    print("Preparing measurement matrix for factorization...")
    W_prepared, row_means, valid_features = sfm.prepare_for_factorization(
        fill_missing=True,
        center_data=True
    )
    
    # Save the prepared measurement matrix
    np.save(f"data/SFM/{prefix}_prepared_matrix.npy", W_prepared)
    print("Saved prepared measurement matrix to 'stanford_bunny_prepared_matrix.npy'")
    
    if row_means is not None:
        np.save(f"data/SFM/{prefix}_row_means.npy", row_means)
        print("Saved row means to 'stanford_bunny_row_means.npy'")
    
    if valid_features is not None:
        np.save(f"data/SFM/{prefix}_valid_features.npy", valid_features)
        print("Saved valid feature indices to 'stanford_bunny_valid_features.npy'")
    
    
    # Show all the figures
    plt.show()


if __name__ == "__main__":
    main()