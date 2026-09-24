"""
Synthetic Authentication Telemetry Dataset Generator
AuthRisk-LR System (REQ-DAT-1, REQ-DAT-2, REQ-DAT-3)
"""

import argparse
import os
import numpy as np
import pandas as pd


def generate_synthetic_data(
    n_samples: int = 10000,
    malicious_ratio: float = 0.15,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Generate statistically realistic authentication telemetry records.

    Features:
        - failed_attempts_5m: (int >= 0)
        - ip_reputation_score: (float [0.0, 1.0]) 0 = clean, 1 = malicious
        - velocity_kmh: (float >= 0.0) km/h between current and prior attempt
        - is_tor_or_vpn: (int {0, 1})
        - country_mismatch: (int {0, 1})
        - hour_anomaly_score: (float [0.0, 1.0])
        - device_trust_score: (float [0.0, 1.0]) 1 = trusted, 0 = untrusted
        - is_compromised: (int {0, 1}) Ground truth binary label
    """
    np.random.seed(random_state)

    n_malicious = int(n_samples * malicious_ratio)
    n_normal = n_samples - n_malicious

    # --- Generate Normal Authentication Records ---
    # Normal users: few failed attempts, clean IP, low velocity, rarely Tor/VPN,
    # rarely country mismatch, normal hours, high device trust
    normal_failed = np.random.poisson(lam=0.4, size=n_normal)
    normal_ip_rep = np.clip(np.random.beta(a=1.5, b=12.0, size=n_normal), 0.0, 1.0)
    normal_velocity = np.clip(np.random.exponential(scale=35.0, size=n_normal), 0.0, 300.0)
    normal_tor = np.random.binomial(n=1, p=0.02, size=n_normal)
    normal_country_mismatch = np.random.binomial(n=1, p=0.04, size=n_normal)
    normal_hour_anomaly = np.clip(np.random.beta(a=1.2, b=6.0, size=n_normal), 0.0, 1.0)
    normal_device_trust = np.clip(np.random.beta(a=8.0, b=1.5, size=n_normal), 0.0, 1.0)
    normal_labels = np.zeros(n_normal, dtype=int)

    # --- Generate Malicious / Compromise Records ---
    # Attacks (brute force, credential stuffing, stolen session):
    # High failed attempts, poor IP reputation, impossible travel speeds,
    # frequent Tor/VPN exit nodes, country mismatch, unusual hours, low device trust
    malicious_failed = np.random.negative_binomial(n=4, p=0.35, size=n_malicious) + 2
    malicious_ip_rep = np.clip(np.random.beta(a=7.0, b=2.0, size=n_malicious), 0.0, 1.0)
    
    # Mix of local attacks and impossible travel attacks
    travel_type = np.random.rand(n_malicious)
    malicious_velocity = np.where(
        travel_type > 0.4,
        np.random.uniform(850.0, 3500.0, size=n_malicious),  # Impossible travel
        np.clip(np.random.exponential(scale=60.0, size=n_malicious), 0.0, 400.0)
    )
    
    malicious_tor = np.random.binomial(n=1, p=0.65, size=n_malicious)
    malicious_country_mismatch = np.random.binomial(n=1, p=0.55, size=n_malicious)
    malicious_hour_anomaly = np.clip(np.random.beta(a=5.0, b=2.5, size=n_malicious), 0.0, 1.0)
    malicious_device_trust = np.clip(np.random.beta(a=1.5, b=6.0, size=n_malicious), 0.0, 1.0)
    malicious_labels = np.ones(n_malicious, dtype=int)

    # Combine data
    df_normal = pd.DataFrame({
        "failed_attempts_5m": normal_failed.astype(int),
        "ip_reputation_score": np.round(normal_ip_rep, 4),
        "velocity_kmh": np.round(normal_velocity, 2),
        "is_tor_or_vpn": normal_tor.astype(int),
        "country_mismatch": normal_country_mismatch.astype(int),
        "hour_anomaly_score": np.round(normal_hour_anomaly, 4),
        "device_trust_score": np.round(normal_device_trust, 4),
        "is_compromised": normal_labels,
    })

    df_malicious = pd.DataFrame({
        "failed_attempts_5m": malicious_failed.astype(int),
        "ip_reputation_score": np.round(malicious_ip_rep, 4),
        "velocity_kmh": np.round(malicious_velocity, 2),
        "is_tor_or_vpn": malicious_tor.astype(int),
        "country_mismatch": malicious_country_mismatch.astype(int),
        "hour_anomaly_score": np.round(malicious_hour_anomaly, 4),
        "device_trust_score": np.round(malicious_device_trust, 4),
        "is_compromised": malicious_labels,
    })

    # Shuffle combined dataset
    df = pd.concat([df_normal, df_malicious], ignore_index=True)
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    # REQ-DAT-3: Ensure zero null, NaN, or non-numeric placeholder values
    assert df.isnull().sum().sum() == 0, "Dataset contains null or NaN values!"
    assert len(df) == n_samples, "Dataset row count mismatch!"

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic cyber authentication telemetry.")
    parser.add_argument("--samples", type=int, default=10000, help="Total sample count (default: 10000)")
    parser.add_argument("--malicious-ratio", type=float, default=0.15, help="Ratio of malicious events (default: 0.15)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "auth_telemetry.csv"),
        help="Target output CSV file path",
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    data = generate_synthetic_data(
        n_samples=args.samples,
        malicious_ratio=args.malicious_ratio,
        random_state=args.seed,
    )
    data.to_csv(args.output, index=False)
    print(f"Generated {len(data)} records -> {args.output}")
    print(f"Malicious class distribution: {data['is_compromised'].mean():.2%}")
