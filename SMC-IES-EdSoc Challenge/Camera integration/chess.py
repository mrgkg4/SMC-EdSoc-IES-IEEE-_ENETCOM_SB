# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 15:41:38 2024

@author: ALA
"""

import cv2
import numpy as np
#import RPi.GPIO as GPIO

# Configuration de la LED
# LED_PIN = 17  # Utiliser la broche GPIO 17 pour la LED
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(LED_PIN, GPIO.OUT)
# GPIO.output(LED_PIN, GPIO.LOW)  # LED éteinte par défaut

# Configuration de l'échiquier
grid = {x: (['.'] * 8)[:] for x in "abcdefgh"}

# Initialisation des pièces sur le damier
def initialize_board():
    global grid
    for i in "abcdefgh":
        grid[i][1] = 'WP'  # Pions blancs
        grid[i][6] = 'BP'  # Pions noirs
    grid['a'][0], grid['h'][0] = 'WR', 'WR'  # Tours blanches
    grid['b'][0], grid['g'][0] = 'WN', 'WN'  # Cavaliers blancs
    grid['c'][0], grid['f'][0] = 'WB', 'WB'  # Fous blancs
    grid['d'][0], grid['e'][0] = 'WQ', 'WK'  # Reine et Roi blancs
    grid['a'][7], grid['h'][7] = 'BR', 'BR'  # Tours noires
    grid['b'][7], grid['g'][7] = 'BN', 'BN'  # Cavaliers noirs
    grid['c'][7], grid['f'][7] = 'BB', 'BB'  # Fous noirs
    grid['d'][7], grid['e'][7] = 'BQ', 'BK'  # Reine et Roi noirs

# Dessiner l'échiquier sur l'image vidéo
def draw_chessboard(frame):
    rows, cols = frame.shape[:2]
    square_size = min(rows, cols) // 8

    for i in range(8):
        for j in range(8):
            top_left = (i * square_size, j * square_size)
            bottom_right = ((i + 1) * square_size, (j + 1) * square_size)
            color = (200, 200, 200) if (i + j) % 2 == 0 else (50, 50, 50)
            cv2.rectangle(frame, top_left, bottom_right, color, -1)

            # Ajouter les pièces
            piece = grid[chr(97 + i)][7 - j]
            if piece != '.':
                cv2.putText(
                    frame, piece,
                    (top_left[0] + square_size // 4, top_left[1] + 3 * square_size // 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA
                )
    return frame

# Fonction pour détecter les mouvements des pièces
def detect_piece_move(prev_frame, current_frame):
    """Détecte le mouvement des pièces entre deux images."""
    diff = cv2.absdiff(prev_frame, current_frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    changes = []
    for contour in contours:
        if cv2.contourArea(contour) > 500:  # Seuil pour ignorer les petits changements
            (x, y, w, h) = cv2.boundingRect(contour)
            changes.append((x + w // 2, y + h // 2))  # Centre du changement
    return changes, thresh  # Retourne aussi l'image binaire de détection

# Convertir les coordonnées du mouvement en notation des échecs
def map_to_chess_square(point, frame_shape):
    """Convertir les coordonnées d'un point en coordonnées de l'échiquier."""
    rows, cols = frame_shape[:2]
    square_size = min(rows, cols) // 8
    x, y = point
    file = chr(ord('a') + x // square_size)
    rank = 8 - y // square_size
    return f"{file}{rank}"

# Vérification de la validité du mouvement
def make_move(player, start, end):
    global grid
    sx, sy = ord(start[0]) - ord('a'), int(start[1]) - 1
    ex, ey = ord(end[0]) - ord('a'), int(end[1]) - 1
    if not (0 <= sx < 8 and 0 <= sy < 8 and 0 <= ex < 8 and 0 <= ey < 8):
        return {'status': 'error', 'message': 'Invalid move'}
    piece = grid[chr(97 + sx)][sy]
    if piece == '.':
        return {'status': 'error', 'message': 'No piece at start'}
    grid[chr(97 + sx)][sy] = '.'
    grid[chr(97 + ex)][ey] = piece
    return {'status': 'success'}
# def make_move(player, start, end):
#     global grid
#     sx, sy = ord(start[0]) - ord('a'), int(start[1]) - 1
#     ex, ey = ord(end[0]) - ord('a'), int(end[1]) - 1
#     if not (0 <= sx < 8 and 0 <= sy < 8 and 0 <= ex < 8 and 0 <= ey < 8):
#         GPIO.output(LED_PIN, GPIO.HIGH)  # Allumer la LED si le mouvement est invalide
#         return {'status': 'error', 'message': 'Invalid move'}
    
#     piece = grid[chr(97 + sx)][sy]
#     if piece == '.':
#         GPIO.output(LED_PIN, GPIO.HIGH)  # Allumer la LED si aucune pièce n'est à la position de départ
#         return {'status': 'error', 'message': 'No piece at start'}
    
#     grid[chr(97 + sx)][sy] = '.'
#     grid[chr(97 + ex)][ey] = piece
#     GPIO.output(LED_PIN, GPIO.LOW)  # Éteindre la LED après un mouvement valide
#     return {'status': 'success'}


# Initialisation de l'échiquier
initialize_board()

# Capture vidéo de la caméra
cap = cv2.VideoCapture(0)

# Vérification si la caméra est correctement ouverte
if not cap.isOpened():
    print("Erreur : la caméra ne peut pas être ouverte.")
    exit()

_, prev_frame = cap.read()

print("Déplacez une pièce et appuyez sur 'q' pour quitter.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Dessiner l'échiquier sur l'image
    frame_with_board = draw_chessboard(frame.copy())

    # Détecter les changements entre les frames
    changes, detected_area = detect_piece_move(prev_frame, frame)
    prev_frame = frame.copy()

    # Si un changement significatif est détecté, on tente de valider le mouvement
    if len(changes) == 2:
        start = map_to_chess_square(changes[0], frame.shape)
        end = map_to_chess_square(changes[1], frame.shape)
        result = make_move('W', start, end)
        print(f"Mouvement détecté: {start} -> {end}")
        print(result)

    # Afficher la vidéo avec l'échiquier
    cv2.imshow('Chessboard', frame_with_board)

    # Afficher la zone de détection des pièces déplacées
    cv2.imshow('Detected Movement', detected_area)

    # Quitter si 'q' est pressé
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
#GPIO.cleanup()  # Nettoyer les configurations GPIO
