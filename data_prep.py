# Importamos las librerías necesarias
from pathlib import Path
import pandas as pd

# Definimos la ruta base del módulo para construir rutas relativas
HERE = Path(__file__).resolve().parent

# Agrupamos las columnas relacionadas para reutilizarlas en agregaciones y así
# evitar duplicados de nombres
SPEND_COLS = ["MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts",
              "MntSweetProducts", "MntGoldProds"]
PURCHASE_COLS = ["NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases"]
CMP_COLS = ["AcceptedCmp1", "AcceptedCmp2", "AcceptedCmp3", "AcceptedCmp4",
            "AcceptedCmp5"]


# Cargamos los datos desde el CSV (separado por tabulador) y tipificamos la
# fecha de alta
def load_data(path: str = "marketing_campaign.csv") -> pd.DataFrame:
    # Construimos la ruta del fichero respecto al directorio del proyecto
    csv_path = HERE / path
    df = pd.read_csv(csv_path, sep="\t")

    # Convertimos la columna de fecha de alta a tipo datetime
    df["Dt_Customer"] = pd.to_datetime(
        df["Dt_Customer"],
        format="%d-%m-%Y",
        errors="coerce",
    )

    return df


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    # Trabajamos sobre una copia para no modificar el DataFrame original
    df = df.copy()

    # Eliminamos columnas constantes porque no aportan variabilidad analítica
    for c in ["Z_CostContact", "Z_Revenue"]:
        if c in df.columns:
            df = df.drop(columns=[c])

    # Construimos las variables agregadas para simplificar los análisis y las
    # visualizaciones
    df["TotalSpend"] = df[SPEND_COLS].sum(axis=1)
    df["TotalPurchases"] = df[PURCHASE_COLS].sum(axis=1)
    df["AcceptedCmp_Total"] = df[CMP_COLS].sum(axis=1)
    df["ChildrenHome"] = df["Kidhome"] + df["Teenhome"]

    # Estimamos la edad al alta a partir del año de alta y el año de nacimiento
    df["Age_at_enroll"] = df["Dt_Customer"].dt.year - df["Year_Birth"]

    return df


def robust_thresholds(df: pd.DataFrame) -> dict:
    # Definimos umbrales robustos (p99.5) para recortar los outliers sin
    # depender de máximos puntuales
    inc_p995 = df["Income"].dropna().quantile(0.995)
    age_p995 = df["Age_at_enroll"].quantile(0.995)
    return {"inc_p995": float(inc_p995), "age_p995": float(age_p995)}
