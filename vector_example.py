import numpy as np

surabaya_coordinates = np.array([-7.2575, 112.7521, 0])
broome_coordinates = np.array([-17.9614, 122.2359, 0])
MBC_coordinates = np.array([-11.691053,118.54483, 99.658104])
f_plasma = 6.53

def latlon_to_cartesian(lat, lon, alt=0):
    R = 6371 + alt
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    x = R * np.cos(lat_rad) * np.cos(lon_rad)
    y = R * np.cos(lat_rad) * np.sin(lon_rad)
    z = R * np.sin(lat_rad)
    return np.array([x, y, z])

def sinesphere(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    distance = np.arccos(np.sin(lat1_rad) * np.sin(lat2_rad) + np.cos(lat1_rad) * np.cos(lat2_rad) * np.cos(lon1_rad - lon2_rad))
    return np.degrees(distance)

def AZ(lat1, lon1, lat2, lon2, dist):
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    dist_rad = np.radians(dist)
    dellon = lon2_rad - lon1_rad
    AZ_val = np.arctan2(np.sin(dellon) * np.cos(lat2_rad) / np.sin(dist_rad), (np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(dist_rad)) / (np.sin(dist_rad) * np.cos(lat1_rad)))
    return np.degrees(AZ_val) % 360


surabaya_cartesian = latlon_to_cartesian(*surabaya_coordinates)
broome_cartesian = latlon_to_cartesian(*broome_coordinates)
MBC_cartesian = latlon_to_cartesian(*MBC_coordinates)

MBC_Broome_vector = MBC_cartesian - broome_cartesian
MBC_Surabaya_vector = MBC_cartesian - surabaya_cartesian

MBC_angle = np.arccos(
    np.dot(MBC_Broome_vector, MBC_Surabaya_vector) /
    (np.linalg.norm(MBC_Broome_vector) * np.linalg.norm(MBC_Surabaya_vector))
)

print(f"Angle at MBC between Broome and Surabaya: {np.degrees(MBC_angle):.2f} degrees")

freq = f_plasma / np.cos(MBC_angle / 2)

print(f"Required frequency for reflection at MBC: {freq:.2f} MHz")

#calc mbc alt from sby
sby_angle = np.arccos(np.dot(MBC_Surabaya_vector, -surabaya_cartesian) / (np.linalg.norm(MBC_Surabaya_vector) * np.linalg.norm(-surabaya_cartesian)))
sby_alt = np.degrees(sby_angle) - 90

dd = sinesphere(surabaya_coordinates[0], surabaya_coordinates[1], MBC_coordinates[0], MBC_coordinates[1])

AZ_sby = AZ(surabaya_coordinates[0], surabaya_coordinates[1], MBC_coordinates[0], MBC_coordinates[1], dd)

print(f"Altitude of MBC from Surabaya's perspective: {sby_alt:.2f} degrees")
print(f"Azimuth of MBC from Surabaya's perspective: {AZ_sby:.2f} degrees")