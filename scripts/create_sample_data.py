#!/usr/bin/env python3
"""
Create sample project data for testing (if you don't have real CSV data yet)
"""

import csv
import random
from datetime import datetime, timedelta

# Sample data
REGIONS = ["Region I", "Region IV-B", "NCR", "Region III"]
PROVINCES = {
    "Region I": ["PANGASINAN", "LA UNION", "ILOCOS NORTE"],
    "Region IV-B": ["PALAWAN", "OCCIDENTAL MINDORO", "ORIENTAL MINDORO"],
    "NCR": ["METRO MANILA"],
    "Region III": ["PAMPANGA", "BULACAN", "TARLAC"],
}
MUNICIPALITIES = {
    "PANGASINAN": ["CITY OF ALAMINOS", "DAGUPAN CITY", "URDANETA CITY"],
    "PALAWAN": ["PUERTO PRINCESA CITY", "CORON", "EL NIDO"],
    "METRO MANILA": ["QUEZON CITY", "MANILA", "MAKATI"],
    "PAMPANGA": ["ANGELES CITY", "SAN FERNANDO", "MABALACAT"],
}
CONTRACTORS = [
    "GED CONSTRUCTION",
    "AZARRAGA CONSTRUCTION",
    "BIG BERTHA CONSTRUCTION",
    "MANILA BUILDERS INC",
    "PACIFIC INFRASTRUCTURE",
]
WORK_TYPES = [
    "Construction of Flood Mitigation Structure",
    "Rehabilitation / Major Repair of Structure",
    "Construction of Line Canal",
    "Slope Protection",
    "Flood Control Dike",
]

# Coordinates (approximate centers)
COORDINATES = {
    "PANGASINAN": (16.0, 120.0),
    "PALAWAN": (9.8, 118.7),
    "METRO MANILA": (14.6, 121.0),
    "PAMPANGA": (15.0, 120.6),
}


def generate_sample_projects(num_projects=100):
    """Generate sample project data"""
    projects = []

    for i in range(num_projects):
        region = random.choice(REGIONS)
        province = random.choice(PROVINCES[region])
        municipality = random.choice(
            MUNICIPALITIES.get(province, [f"{province} CITY"])
        )
        contractor = random.choice(CONTRACTORS)
        work_type = random.choice(WORK_TYPES)

        # Generate coordinates with some randomness
        base_coords = COORDINATES.get(province, (12.0, 121.0))
        lat = base_coords[0] + random.uniform(-0.5, 0.5)
        lon = base_coords[1] + random.uniform(-0.5, 0.5)

        # Generate budget
        abc = random.randint(2000000, 20000000)
        contract_cost = abc * random.uniform(0.85, 0.98)

        # Generate dates
        year = random.choice([2023, 2024, 2025])
        start_date = datetime(year, random.randint(1, 12), random.randint(1, 28))
        completion_date = start_date + timedelta(days=random.randint(180, 540))

        project = {
            "ObjectId": i + 1,
            "ProjectID": f"P{random.randint(100000, 999999):06d}LZ",
            "ProjectComponentID": f"P{random.randint(100000, 999999):06d}LZ_{year}AG{i:04d}",
            "ContractID": f"{year}AG{i:04d}",
            "Region": region,
            "Province": province,
            "Municipality": municipality,
            "LegislativeDistrict": f"{province} (FIRST LEGISLATIVE DISTRICT)",
            "Latitude": lat,
            "Longitude": lon,
            "latitude": lat,
            "longitude": lon,
            "ABC": abc,
            "ABC_String": f"₱{abc:,.2f}",
            "ContractCost": contract_cost,
            "ContractCost_String": f"₱{contract_cost:,.2f}",
            "Contractor": contractor,
            "DistrictEngineeringOffice": f"{province} District Engineering Office",
            "ImplementingOffice": f"{province} District Engineering Office",
            "ProjectDescription": f"{work_type} at {municipality}",
            "ProjectComponentDescription": f"Component {i+1}",
            "TypeofWork": work_type,
            "infra_type": "Flood Control",
            "Program": "Flood Management Program",
            "FundingYear": year,
            "InfraYear": year,
            "CompletionYear": completion_date.year,
            "StartDate": start_date.isoformat(),
            "CompletionDateOriginal": completion_date.isoformat(),
            "CompletionDateActual": completion_date.isoformat()
            if random.random() > 0.3
            else "",
            "CreationDate": datetime.now().isoformat(),
            "Creator": "admin",
            "EditDate": datetime.now().isoformat(),
            "Editor": "admin",
            "GlobalID": f"{{{random.randint(10**31, 10**32-1):032X}}}",
        }

        projects.append(project)

    return projects


def main():
    """Generate and save sample data"""
    print("Generating sample project data...")

    projects = generate_sample_projects(100)

    # Write to CSV
    output_file = "data/flood_control__floodcontrol_data__0__20251004_233415.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        if projects:
            writer = csv.DictWriter(f, fieldnames=projects[0].keys())
            writer.writeheader()
            writer.writerows(projects)

    print(f"✓ Generated {len(projects)} sample projects")
    print(f"✓ Saved to: {output_file}")
    print("\nNext steps:")
    print("  1. Run: python scripts/setup_vectordb.py")
    print("  2. Run: python scripts/embed_projects.py")
    print("  3. Start server: uvicorn backend.main:app --reload")


if __name__ == "__main__":
    main()