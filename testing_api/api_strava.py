import requests
from collections import defaultdict
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import rcParams
from datetime import datetime, timedelta
import csv
from pathlib import Path
import pandas as pd

# --- Configuración ---
client_id = '184167'
client_secret = '873e9ab50d3315c172338512175dfbf3988bb9b3'
refresh_token = '3ac758488a082c57039ed2b4cc09b0e513c7e640'
club_id = 1793883

def refresh_access_token():
    resp = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
    )
    if resp.status_code == 200:
        data = resp.json()
        print("Token renovado correctamente")
        return data['access_token'], data['refresh_token']
    else:
        print('Fallo al renovar token:', resp.text)
        return None, None
    
def get_club_info(token, club_id):
    url = f'https://www.strava.com/api/v3/clubs/{club_id}'
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Error obteniendo datos del club: {resp.status_code}, {resp.text}")
        return {}

def get_club_members(token, club_id, per_page=200):
    url = f'https://www.strava.com/api/v3/clubs/{club_id}/members'
    headers = {'Authorization': f'Bearer {token}'}
    members = []
    page = 1
    while True:
        params = {'per_page': per_page, 'page': page}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        members.extend(data)
        page += 1
    return members

def get_club_activities(token, club_id, per_page=200):
    url = f'https://www.strava.com/api/v3/clubs/{club_id}/activities'
    headers = {'Authorization': f'Bearer {token}'}
    actividades = []
    page = 1
    while True:
        params = {'per_page': per_page, 'page': page}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            break
        datos = resp.json()
        if not datos:
            break
        actividades.extend(datos)
        page += 1
    return actividades

def total_kms_por_atleta(actividades):
    resumen = defaultdict(float)
    for act in actividades:
        atleta = f"{act.get('athlete_firstname', 'Desconocido')} {act.get('athlete_lastname', '')}"
        try:
            metros = float(act.get('distance', 0))
        except (TypeError, ValueError):
            metros = 0.0
        kms = metros / 1000.0
        resumen[atleta] += kms
    return resumen

def mostrar_info_club(club_data):
    print(f"Nombre Club: {club_data.get('name', '')}")
    print(f"Descripción: {club_data.get('description', '')}")
    print(f"Ciudad: {club_data.get('city', '')}, País: {club_data.get('country', '')}")
    print(f"Tipo: {club_data.get('sport_type', '')}")
    print(f"Miembros totales: {club_data.get('member_count', 'na')}")

def mostrar_miembros(miembros):
    for m in miembros:
        nombre = m.get('firstname', '') + ' ' + m.get('lastname', '')
        print(f"{nombre}")

def graficar_kms_por_miembro(resumen):
    atletas = sorted(resumen.items(), key=lambda x: x[1], reverse=True)
    nombres = [a[0] for a in atletas]
    kms = [a[1] for a in atletas]
    plt.figure(figsize=(12, 6))
    plt.barh(nombres, kms, color='skyblue')
    plt.xlabel('Kilómetros')
    plt.ylabel('Miembro')
    plt.title('Kilómetros recorridos por cada miembro')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

def mostrar_kms_totales_por_atleta(resumen):
    for atleta, kms in resumen.items():
        print(f"{atleta}: {kms:.2f} km")

def graficar_caja_con_leaderboard(resumen):
    total_kms = sum(resumen.values())
    top5 = sorted(resumen.items(), key=lambda x: x[1], reverse=True)[:5]
    max_kms = 1000
    pct_avance = min(total_kms / max_kms, 1.0)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')
    ax.set_xlim(-1, 7)
    ax.set_ylim(-50, 1050)
    ax.add_patch(Rectangle((0, 0), 3, max_kms, fill=True, facecolor='#f5f5f5', edgecolor='#666', linewidth=2, zorder=1))
    ax.add_patch(Rectangle((0, 0), 3, pct_avance * max_kms, fill=True, facecolor='#1565c0', alpha=0.8, zorder=2))
    ax.add_patch(Rectangle((0, 0), 3, max_kms, fill=False, edgecolor='#222', linewidth=1, zorder=3))
    ax.text(1.5, max_kms / 2, f"{total_kms:.1f} km", ha="center", va="center", fontsize=44, color="#263238", fontweight="bold")
    ax.text(1.5, max_kms + 40, "Total recorrido", ha="center", va="bottom", fontsize=20, color="#1565c0")
    ax.text(1.5, -35, "Meta: 1000 km", ha="center", va="top", fontsize=14, color="#666")
    ax.plot([3.5,3.5],[0,max_kms],linestyle="--",color="#bdbdbd",linewidth=2,zorder=1)
    ax.text(4.2, max_kms - 20, "Top 5 del club:", fontsize=18, fontweight='bold', va='top', color="#1565c0")
    for i, (nombre, kms) in enumerate(top5):
        ax.text(4.2, max_kms - 100 - i*70, f"{i+1}. {nombre}: {kms:.1f} km", fontsize=16, va='top', color="#263238")
    
    plt.tight_layout()
    plt.show()

def guardar_actividad(actividades, ruta_csv="actividades_club.csv"):
    ruta = Path(ruta_csv)
    COLUMNS = [
        'athlete_firstname',
        'athlete_lastname',
        'activity_name',
        'distance',
        'moving_time',
        'elapsed_time',
        'total_elevation_gain',
        'type',
        'sport_type',
        'workout_type',
        'device_name',
    ]

    UNIQUE_KEY_COLS = [
        'athlete_firstname',
        'athlete_lastname',
        'activity_name',
        'distance',
        'moving_time',
    ]

    def _clave_unica_from_row(row):
        return "|".join(row.get(col, "") for col in UNIQUE_KEY_COLS)

    def _clave_unica_from_fila(fila):
        return "|".join(str(fila.get(col, "")) for col in UNIQUE_KEY_COLS)
    
    claves_existentes = set()
    archivo_ya_existia = ruta.exists()
    if archivo_ya_existia:
        with ruta.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                clave = _clave_unica_from_row(row)
                claves_existentes.add(clave)

    with ruta.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if not archivo_ya_existia:
            writer.writeheader()

        for actividad in actividades:
            atleta = actividad.get('athlete', {}) or {}
            fila = {
                'athlete_firstname': atleta.get('firstname'),
                'athlete_lastname': atleta.get('lastname'),
                'activity_name': actividad.get('name'),
                'distance': actividad.get('distance'),
                'moving_time': actividad.get('moving_time'),
                'elapsed_time': actividad.get('elapsed_time'),
                'total_elevation_gain': actividad.get('total_elevation_gain'),
                'type': actividad.get('type'),
                'sport_type': actividad.get('sport_type'),
                'workout_type': actividad.get('workout_type'),
                'device_name': actividad.get('device_name'),
            }

            clave_nueva = _clave_unica_from_fila(fila)
            if clave_nueva in claves_existentes:
                continue

            writer.writerow(fila)
            claves_existentes.add(clave_nueva)

# --- MAIN ---
if __name__ == "__main__":
    # Renovar el token si es necesario (opcional)
    access_token, refresh_token = refresh_access_token()

    # 1. Info general del club
    club_data = get_club_info(access_token, club_id)
    # mostrar_info_club(club_data)

    # 2. Miembros del club
    miembros = get_club_members(access_token, club_id)
    # mostrar_miembros(miembros)

    # 3. Actividades y resumen por atleta
    last_activities = get_club_activities(access_token, club_id)
    print(len(last_activities))
    guardar_actividad(last_activities, "actividades_club.csv")
    activities= pd.read_csv("actividades_club.csv").to_dict(orient='records')
    resumen = total_kms_por_atleta(activities)
    # mostrar_kms_totales_por_atleta(resumen)
    graficar_kms_por_miembro(resumen)
    graficar_caja_con_leaderboard(resumen)


