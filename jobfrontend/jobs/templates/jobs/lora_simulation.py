import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# 🌍 Ground nodes
ground_nodes = {
    "Rome": (-3000, 0),
    "Milan": (3000, 0),
    "NodeRM": (0, -3000)  # Only receives, no transmission
}

# 🛰️ Satellite positions (initial)
num_sats = 6
sat_positions = np.array([
    [-2000, 5000], [0, 6000], [2000, 5000],  # Satellites above
    [-2500, 6500], [2500, 6500], [0, 7000]   # Satellites farther
])
sat_velocity = np.array([
    [50, -5], [-50, -5], [30, -5], 
    [-40, -5], [40, -5], [0, -5]   # Simulating movement
])

# 📡 Transmission logic
packet_paths = []
received_packets = []
collisions = set()
elevation_threshold = 20  # Degrees

# 📡 Simulated packet transmissions from Rome & Milan
for node, pos in ground_nodes.items():
    if node != "NodeRM":  # Only Rome & Milan transmit
        for sat_id in range(num_sats):
            elevation_angle = np.random.randint(10, 60)  # Random elevation
            delay = np.random.uniform(0.1, 1.0)  # Simulated transmission delay
            
            if elevation_angle >= elevation_threshold:
                packet_paths.append((pos, sat_positions[sat_id], sat_id, delay))
            else:
                print(f"❌ {node} → Sat {sat_id}: Missed (Low Elevation {elevation_angle}°)")

# 🎬 Animation setup
fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(-4000, 4000)
ax.set_ylim(-4000, 8000)
ax.set_title("LoRaWAN LR-FHSS Satellite Simulation")

# 📍 Draw Ground Nodes
node_plots = {name: ax.plot([], [], 'go', markersize=10)[0] for name in ground_nodes}
for name, (x, y) in ground_nodes.items():
    ax.text(x + 200, y + 200, name, fontsize=12)

# 🛰️ Draw Satellites
sat_plots = [ax.plot([], [], 'bo', markersize=8)[0] for _ in range(num_sats)]
sat_texts = [ax.text(0, 0, f"Sat {i+1}", fontsize=10) for i in range(num_sats)]

# 📡 Packets
packet_lines = [ax.plot([], [], 'r--', alpha=0.5)[0] for _ in range(len(packet_paths))]

# 🔄 Animation function
def update(frame):
    global sat_positions
    sat_positions[:] += sat_velocity  # Move satellites

    # Update satellite positions
    for i, sat_plot in enumerate(sat_plots):
        sat_plot.set_data(sat_positions[i, 0], sat_positions[i, 1])
        sat_texts[i].set_position((sat_positions[i, 0] + 100, sat_positions[i, 1] + 100))

    # Update packet transmissions
    for i, (start, end, sat_id, delay) in enumerate(packet_paths):
        if frame * 0.1 > delay:  # Delay before transmission
            if np.linalg.norm(sat_positions[sat_id] - start) < 3000:
                packet_lines[i].set_data([start[0], sat_positions[sat_id, 0]], [start[1], sat_positions[sat_id, 1]])
                received_packets.append((sat_id, start))
            else:
                packet_lines[i].set_data([], [])

    # 🚀 Check for Collisions
    collision_sats = set()
    for i in range(len(received_packets)):
        for j in range(i + 1, len(received_packets)):
            if received_packets[i][0] == received_packets[j][0]:  # Same satellite
                collision_sats.add(received_packets[i][0])
    
    # 🔴 Mark Collisions
    for sat_id in collision_sats:
        collisions.add(sat_id)
        sat_plots[sat_id].set_color('red')

    return sat_plots + sat_texts + packet_lines

# 🎬 Run Animation
ani = animation.FuncAnimation(fig, update, frames=100, interval=100)
plt.show()
