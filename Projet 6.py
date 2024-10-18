import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc

#########################################
wCam, hCam = 640, 480
#########################################

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

detector = htm.handDetector(detectionCon=0.7)

# Initialisation pour le contrôle du son
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0
isMuted = False
swipeStart = None  # Point de départ pour détecter un geste de balayage

# Initialisation pour le contrôle de la luminosité
brightness = sbc.get_brightness()
brightnessBar = 400
brightnessPer = brightness[0]

# Variable pour gérer le mode actuel (volume ou luminosité)
mode = None  # 'volume' ou 'luminosité'

# Définir les zones de sélection pour les gestes
select_volume_zone = (50, 50, 150, 150)  # Coordonnées pour la zone de sélection du volume
select_brightness_zone = (wCam - 150, 50, wCam - 50, 150)  # Zone de sélection de la luminosité

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)

    # Dessiner les zones de sélection
    cv2.rectangle(img, select_volume_zone[0:2], select_volume_zone[2:4], (0, 0, 255), 2)
    cv2.putText(img, 'Volume', (select_volume_zone[0] + 10, select_volume_zone[1] - 10), 
                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
    cv2.rectangle(img, select_brightness_zone[0:2], select_brightness_zone[2:4], (0, 255, 255), 2)
    cv2.putText(img, 'Luminosite', (select_brightness_zone[0] + 10, select_brightness_zone[1] - 10), 
                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 2)

    if len(lmList) != 0:
        x1, y1 = lmList[8][1], lmList[8][2]  # Coordonnées du doigt (index)
        x2, y2 = lmList[4][1], lmList[4][2]  # Coordonnées du pouce

        # Tracer la ligne entre le pouce et l'index
        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 3)

        # Vérifier si le doigt pointe sur une zone de sélection
        if select_volume_zone[0] < x1 < select_volume_zone[2] and select_volume_zone[1] < y1 < select_volume_zone[3]:
            mode = 'volume'  # Activer le mode de contrôle du volume
            cv2.putText(img, 'Mode: Volume', (200, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)

        elif select_brightness_zone[0] < x1 < select_brightness_zone[2] and select_brightness_zone[1] < y1 < select_brightness_zone[3]:
            mode = 'luminosité'  # Activer le mode de contrôle de la luminosité
            cv2.putText(img, 'Mode: Luminosite', (200, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 3)

        if mode == 'volume':
            # **Contrôle du volume**
            length = math.hypot(x2 - x1, y2 - y1)

            vol = np.interp(length, [50, 300], [minVol, maxVol])
            volBar = np.interp(length, [50, 300], [400, 150])
            volPer = np.interp(length, [50, 300], [0, 100])
            volume.SetMasterVolumeLevel(vol, None)

            # Swipe pour mute/unmute
            if swipeStart is None:
                swipeStart = (x1, y1)
            else:
                swipeDistance = x1 - swipeStart[0]
                if abs(swipeDistance) > 100:
                    isMuted = not isMuted
                    volume.SetMasterVolumeLevel(minVol if isMuted else vol, None)
                    swipeStart = None  # Réinitialiser après le geste

            # Barre de volume
            cv2.rectangle(img, (50, 150), (85, 400), (0, 0, 255), 3)
            cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 0, 255), cv2.FILLED)
            cv2.putText(img, f'{int(volPer)}%', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)

        elif mode == 'luminosité':
            # **Contrôle de la luminosité**
            length = math.hypot(x2 - x1, y2 - y1)

            brightnessPer = np.interp(length, [50, 300], [0, 100])
            brightnessBar = np.interp(length, [50, 300], [400, 150])
            sbc.set_brightness(int(brightnessPer))

            # Barre de luminosité
            cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 255), 3)
            cv2.rectangle(img, (50, int(brightnessBar)), (85, 400), (0, 255, 255), cv2.FILLED)
            cv2.putText(img, f'{int(brightnessPer)}%', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 3)

        # Cercle pulsant pour un retour visuel
        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)

    cTime = time.time()
    pTime = cTime

    cv2.imshow("Img", img)
    cv2.waitKey(1)
