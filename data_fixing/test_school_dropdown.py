"""
Test script to show what the school dropdown will display
"""

from database_utils import get_database_connection, get_active_schools, get_active_regions

engine = get_database_connection()

print("=" * 60)
print("SCHOOL DROPDOWN TEST")
print("=" * 60)

regions = get_active_regions(engine)

print(f"\n📍 Available Regions: {len(regions)}")
for region in regions:
    print(f"   - {region}")

print("\n" + "=" * 60)

for region in regions:
    print(f"\n🏫 Schools in {region}:")
    print("-" * 60)
    
    schools = get_active_schools(engine, region_id=region)
    
    if schools:
        for school in schools:
            # This is what will appear in the dropdown
            dropdown_text = f"{school['school_id']} - {school['school_name']}"
            print(f"   ✓ {dropdown_text}")
    else:
        print(f"   (No schools found)")

print("\n" + "=" * 60)
print("This is what users will see in the dropdown!")
print("=" * 60)


