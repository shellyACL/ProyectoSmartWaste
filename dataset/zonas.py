import requests
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://sitservicios.lapaz.bo/geoserver/wfs"

params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": "catastro:zonas",
    "outputFormat": "application/json"
}

r = requests.get(
    url,
    params=params,
    verify=False,
    timeout=120
)

data = r.json()

zonas = []

for feature in data["features"]:
    props = feature["properties"]

    zonas.append({
        "codigo": props["GDBSCODB"],
        "zona": props["GDBSNOMB"]
    })

df = pd.DataFrame(zonas)

# eliminar duplicados
df = df.drop_duplicates(subset=["zona"])

# ordenar alfabéticamente
df = df.sort_values("zona")

# guardar
df.to_csv(
    "zonas_lapaz.csv",
    index=False,
    encoding="utf-8-sig"
)

print(f"Total zonas: {len(df)}")
print(df.head(20))