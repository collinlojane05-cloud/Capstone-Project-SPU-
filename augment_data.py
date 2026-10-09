import pandas as pd
import numpy as np

def add_jitter(df, columns, noise_level=0.05):
    """Adds random Gaussian noise to simulate sensor inaccuracies."""
    jittered = df.copy()
    # Generate random noise matching the shape of our sensor data
    noise = np.random.normal(loc=0.0, scale=noise_level, size=(len(df), len(columns)))
    jittered[columns] = jittered[columns] + noise
    
    # Tag the session ID so we know it's synthetic
    jittered['session_id'] = jittered['session_id'].astype(str) + "_jittered"
    return jittered

def apply_scaling(df, columns, scaling_factor=0.1):
    """Multiplies data by a random scalar to simulate different movement intensities."""
    scaled = df.copy()
    # Generate a random scalar near 1.0 (e.g., 0.95 or 1.05) for each axis
    scalars = np.random.normal(loc=1.0, scale=scaling_factor, size=len(columns))
    scaled[columns] = scaled[columns] * scalars
    
    # Tag the session ID
    scaled['session_id'] = scaled['session_id'].astype(str) + "_scaled"
    return scaled

if __name__ == "__main__":
    print("Loading original data...")
    # 1. Load the raw data
    df = pd.read_csv('sensor_data.csv')
    sensor_cols = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']

    # Keep the original data in our final list
    augmented_dfs = [df] 

    # 2. Group by session_id to process each recording independently
    grouped = df.groupby('session_id')
    print(f"Found {len(grouped)} original sessions. Applying transformations...")

    for session_id, session_data in grouped:
        # Generate and append a jittered version
        df_jittered = add_jitter(session_data, sensor_cols, noise_level=0.03)
        augmented_dfs.append(df_jittered)
        
        # Generate and append a scaled version
        df_scaled = apply_scaling(session_data, sensor_cols, scaling_factor=0.1)
        augmented_dfs.append(df_scaled)

    # 3. Combine everything into one massive DataFrame
    final_df = pd.concat(augmented_dfs, ignore_index=True)

    # 4. Save the new dataset
    final_df.to_csv('sensor_data_augmented.csv', index=False)
    
    print("Augmentation complete!")
    print(f"Original rows: {len(df)}")
    print(f"New rows: {len(final_df)}")