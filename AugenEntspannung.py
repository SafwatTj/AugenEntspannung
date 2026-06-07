import pygame
import sys
import math
import random

# ===== FARBEN =====
DUNKEL_GRAU = (30, 30, 35)
GRUEN = (60, 180, 60)
GRUEN_HELL = (100, 220, 100)
GELB = (200, 180, 60)
GELB_GOLD = (220, 200, 80)  # Жёлто-золотистый для звёзд
GELB_WEICH = (200, 190, 70)
ROT = (200, 60, 60)
GRAU = (80, 80, 80)
GRAU_HELL = (120, 120, 120)
WEISS = (220, 220, 220)
SCHWARZ = (0, 0, 0)
BLAU = (60, 100, 200)

# ===== KONSTANTEN =====
STANDARD_BREITE = 900
STANDARD_HOEHE = 700
MODI = {
    "30s": 30,
    "60s": 60,
    "120s": 120
}
MODI_NAMEN = {
    "30s": "SCHNELL",
    "60s": "STANDARD",
    "120s": "TIEF"
}


# ===== STERNE (goldgelb, wissenschaftlich optimal) =====
class Stern:
    def __init__(self, breite, hoehe):
        self.x = random.randint(0, breite)
        self.y = random.randint(0, hoehe)
        self.radius = random.randint(2, 5)
        self.helligkeit = random.randint(150, 220)
        self.geschwindigkeit = random.uniform(0.5, 3.0)
        self.blink_phase = random.uniform(0, math.pi * 2)

    def zeichnen(self, fenster, zeit):
        # Goldgelbe Farbe mit Helligkeitspulsation
        blink = int(self.helligkeit * (0.5 + 0.5 * math.sin(zeit * 2 + self.blink_phase)))
        # Basis: Goldgelb (220, 200, 80), variiert mit Helligkeit
        r = min(255, 180 + blink // 3)
        g = min(255, 160 + blink // 2)
        b = min(255, 60 + blink // 5)
        farbe = (r, g, b)
        pygame.draw.circle(fenster, farbe, (int(self.x), int(self.y)), self.radius)
        # Heller Kern
        if self.radius > 3:
            pygame.draw.circle(fenster, (255, 235, 150), (int(self.x), int(self.y)), self.radius // 2)

    def bewegen(self, richtung_x, richtung_y, breite, hoehe):
        self.x += richtung_x * self.geschwindigkeit
        self.y += richtung_y * self.geschwindigkeit
        if self.x < 0:
            self.x = breite
        if self.x > breite:
            self.x = 0
        if self.y < 0:
            self.y = hoehe
        if self.y > hoehe:
            self.y = 0


# ===== KNOEPFE =====
class Knopf:
    def __init__(self, x, y, breite, hoehe, text, farbe_normal, farbe_hover, farbe_text):
        self.rechteck = pygame.Rect(x, y, breite, hoehe)
        self.text = text
        self.farbe_normal = farbe_normal
        self.farbe_hover = farbe_hover
        self.farbe_text = farbe_text
        self.aktiv = True
        self.ausgewaehlt = False
        self.click_animation = 0

    def zeichnen(self, fenster, schrift):
        farbe = self.farbe_hover if self.ist_hover() else self.farbe_normal
        if not self.aktiv:
            farbe = GRAU
        if self.ausgewaehlt:
            farbe = GRUEN_HELL

        rechteck_temp = self.rechteck.copy()
        if self.click_animation > 0:
            self.click_animation -= 1
            rechteck_temp.inflate_ip(-5, -5)

        pygame.draw.rect(fenster, farbe, rechteck_temp, border_radius=8)
        pygame.draw.rect(fenster, WEISS, rechteck_temp, 2, border_radius=8)

        text_oberfl = schrift.render(self.text, True, self.farbe_text)
        text_x = rechteck_temp.x + rechteck_temp.width // 2 - text_oberfl.get_width() // 2
        text_y = rechteck_temp.y + rechteck_temp.height // 2 - text_oberfl.get_height() // 2
        fenster.blit(text_oberfl, (text_x, text_y))

    def ist_hover(self):
        maus = pygame.mouse.get_pos()
        return self.rechteck.collidepoint(maus)

    def klick(self, maus_pos):
        return self.rechteck.collidepoint(maus_pos) and self.aktiv

    def animiere_click(self):
        self.click_animation = 5


# ===== ANIMATION =====
class Animation:
    def __init__(self, dauer_sekunden):
        self.dauer = dauer_sekunden
        self.start_zeit = None
        self.aktiv = False
        self.pausiert = False
        self.pause_start = None
        self.vergangene_pause = 0

    def starten(self):
        self.start_zeit = pygame.time.get_ticks()
        self.aktiv = True
        self.pausiert = False

    def stoppen(self):
        self.aktiv = False
        self.pausiert = False

    def pausieren(self):
        if self.aktiv and not self.pausiert:
            self.pausiert = True
            self.pause_start = pygame.time.get_ticks()

    def fortsetzen(self):
        if self.aktiv and self.pausiert:
            self.vergangene_pause += pygame.time.get_ticks() - self.pause_start
            self.pausiert = False

    def ist_fertig(self):
        if not self.aktiv:
            return False
        if self.pausiert:
            return False
        vergangen = (pygame.time.get_ticks() - self.start_zeit - self.vergangene_pause) / 1000.0
        return vergangen >= self.dauer

    def verbleibende_zeit(self):
        if not self.aktiv:
            return 0
        if self.pausiert:
            vergangen = (self.pause_start - self.start_zeit - self.vergangene_pause) / 1000.0
        else:
            vergangen = (pygame.time.get_ticks() - self.start_zeit - self.vergangene_pause) / 1000.0
        return max(0, self.dauer - vergangen)

    def zeichnen(self, fenster, breite, hoehe, sterne, zeit):
        if not self.aktiv:
            return

        vergangen = (pygame.time.get_ticks() - self.start_zeit - self.vergangene_pause) / 1000.0
        t = vergangen / self.dauer

        mitte_x = breite // 2
        mitte_y = hoehe // 2

        # Sterne bewegen (zum Zentrum)
        richtung_x = (mitte_x - breite / 2) * 0.03
        richtung_y = (mitte_y - hoehe / 2) * 0.03
        for stern in sterne:
            stern.bewegen(richtung_x, richtung_y, breite, hoehe)
            stern.zeichnen(fenster, zeit)

        # Phase 1: Tunnel (0-40% der Zeit)
        phase1_ende = 0.4
        if t < phase1_ende:
            faktor = math.pow(t / phase1_ende, 0.7)
            max_radius = int(min(breite, hoehe) * 0.45)
            anzahl_kreise = 30

            for i in range(anzahl_kreise):
                radius = int(max_radius * (1 - i / anzahl_kreise) * (0.15 + faktor * 0.85))
                farb_wert = int(40 + 160 * (1 - i / anzahl_kreise))
                farbe = (25, farb_wert, 25)
                pygame.draw.circle(fenster, farbe, (mitte_x, mitte_y), radius, 2)
                if i % 3 == 0:
                    pygame.draw.circle(fenster, (farb_wert // 2, farb_wert, farb_wert // 2), (mitte_x, mitte_y),
                                       radius - 2, 1)

        # Peripherie Bewegung
        peripherie_intensitaet = math.sin(pygame.time.get_ticks() * 0.014) * 0.5 + 0.5
        for winkel in range(0, 360, 25):
            rad = math.radians(winkel + peripherie_intensitaet * 30)
            x1 = mitte_x + int(min(breite, hoehe) * 0.38 * math.cos(rad))
            y1 = mitte_y + int(min(breite, hoehe) * 0.38 * math.sin(rad))
            x2 = mitte_x + int(min(breite, hoehe) * 0.50 * math.cos(rad))
            y2 = mitte_y + int(min(breite, hoehe) * 0.50 * math.sin(rad))
            farb_wert = int(100 + 120 * peripherie_intensitaet)
            pygame.draw.line(fenster, (farb_wert // 2, farb_wert, farb_wert // 2), (x1, y1), (x2, y2), 4)

        # Farbpulsation (Gelb -> Gruen)
        if t > 0.35:
            puls = math.sin(pygame.time.get_ticks() * 0.008) * 0.5 + 0.5
            r = int(200 + 40 * puls)
            g = int(200 - 70 * puls)
            b = int(50 + 40 * puls)
            kreis_radius = int(min(breite, hoehe) * 0.30)
            pygame.draw.circle(fenster, (r, g, b), (mitte_x, mitte_y), kreis_radius, 5)
            kreis_radius_kern = int(min(breite, hoehe) * 0.10 * (0.8 + 0.4 * puls))
            pygame.draw.circle(fenster, (r, g, b), (mitte_x, mitte_y), kreis_radius_kern, 2)


# ===== WARNUNG =====
def zeige_warnung(fenster, breite, hoehe):
    fenster.fill(DUNKEL_GRAU)

    titel = pygame.font.Font(None, 48).render("ACHTUNG - WARNUNG", True, ROT)
    fenster.blit(titel, (breite // 2 - titel.get_width() // 2, 80))

    zeilen = [
        "Diese Programm ist NUR zur Entspannung der Augen gedacht.",
        "",
        "NICHT verwenden bei:",
        "• Epilepsie (lichtempfindliche Form)",
        "• Glaukom (Gruener Star)",
        "• Netzhautablösung (in der Vorgeschichte)",
        "• Akuten Augenentzuendungen",
        "",
        "Bei Schmerzen, Schwindel oder Sehverschlechterung -> STOP druecken",
        "und einen Augenarzt aufsuchen.",
        "",
        "Dies ist kein medizinisches Geraet.",
        "",
        "Druecken Sie eine beliebige Taste zum Fortfahren..."
    ]

    y = 180
    for zeile in zeilen:
        text = pygame.font.Font(None, 24).render(zeile, True, WEISS)
        fenster.blit(text, (100, y))
        y += 32

    pygame.display.flip()

    warten = True
    while warten:
        for ereignis in pygame.event.get():
            if ereignis.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ereignis.type == pygame.KEYDOWN:
                warten = False


# ===== HAUPTFUNKTION =====
def main():
    pygame.init()

    fenster = pygame.display.set_mode((STANDARD_BREITE, STANDARD_HOEHE), pygame.RESIZABLE)
    pygame.display.set_caption("AugenEntspannung - Safwat Burkhonov")

    schrift_gross = pygame.font.Font(None, 64)
    schrift_normal = pygame.font.Font(None, 32)
    schrift_klein = pygame.font.Font(None, 20)

    zeige_warnung(fenster, STANDARD_BREITE, STANDARD_HOEHE)

    sterne = [Stern(STANDARD_BREITE, STANDARD_HOEHE) for _ in range(120)]

    gewaehlter_modus = None
    animation = None
    laeuft = True
    uhr = pygame.time.Clock()
    puls_zeit = 0
    pausiert = False

    while laeuft:
        breite, hoehe = fenster.get_size()
        zeit = pygame.time.get_ticks() / 1000.0

        button_breite = 105
        button_hoehe = 50
        abstand = 12
        gesamt_breite = button_breite * 6 + abstand * 5
        start_x = (breite - gesamt_breite) // 2
        y = hoehe - 85

        button_30 = Knopf(start_x, y, button_breite, button_hoehe, "30s", GRAU, GRAU_HELL, WEISS)
        button_60 = Knopf(start_x + (button_breite + abstand) * 1, y, button_breite, button_hoehe, "60s", GRAU,
                          GRAU_HELL, WEISS)
        button_120 = Knopf(start_x + (button_breite + abstand) * 2, y, button_breite, button_hoehe, "2min", GRAU,
                           GRAU_HELL, WEISS)
        button_start = Knopf(start_x + (button_breite + abstand) * 3, y, button_breite, button_hoehe, "START", GRUEN,
                             GRUEN_HELL, SCHWARZ)
        button_stop = Knopf(start_x + (button_breite + abstand) * 4, y, button_breite, button_hoehe, "STOP", ROT,
                            (220, 80, 80), WEISS)
        button_pause = Knopf(start_x + (button_breite + abstand) * 5, y, button_breite, button_hoehe, "PAUSE", BLAU,
                             (100, 140, 240), WEISS)

        button_30.ausgewaehlt = (gewaehlter_modus == "30s")
        button_60.ausgewaehlt = (gewaehlter_modus == "60s")
        button_120.ausgewaehlt = (gewaehlter_modus == "120s")

        if gewaehlter_modus is None:
            button_start.aktiv = False
        else:
            button_start.aktiv = (animation is None or not animation.aktiv)

        button_pause.aktiv = (animation is not None and animation.aktiv)

        for ereignis in pygame.event.get():
            if ereignis.type == pygame.QUIT:
                laeuft = False

            if ereignis.type == pygame.KEYDOWN:
                if ereignis.key == pygame.K_ESCAPE:
                    laeuft = False
                if ereignis.key == pygame.K_p:
                    if animation and animation.aktiv:
                        if pausiert:
                            animation.fortsetzen()
                            pausiert = False
                        else:
                            animation.pausieren()
                            pausiert = True
                if not animation or not animation.aktiv:
                    if ereignis.key == pygame.K_1:
                        gewaehlter_modus = "30s"
                        button_30.animiere_click()
                    if ereignis.key == pygame.K_2:
                        gewaehlter_modus = "60s"
                        button_60.animiere_click()
                    if ereignis.key == pygame.K_3:
                        gewaehlter_modus = "120s"
                        button_120.animiere_click()
                if ereignis.key == pygame.K_RETURN or ereignis.key == pygame.K_SPACE:
                    if button_start.aktiv and gewaehlter_modus and (not animation or not animation.aktiv):
                        animation = Animation(MODI[gewaehlter_modus])
                        animation.starten()
                        pausiert = False
                        button_start.animiere_click()
                if ereignis.key == pygame.K_s or ereignis.key == pygame.K_0:
                    if animation and animation.aktiv:
                        animation.stoppen()
                        animation = None
                        pausiert = False
                        button_stop.animiere_click()

            if ereignis.type == pygame.MOUSEBUTTONDOWN:
                maus_pos = pygame.mouse.get_pos()

                if button_30.klick(maus_pos) and (not animation or not animation.aktiv):
                    gewaehlter_modus = "30s"
                    button_30.animiere_click()
                if button_60.klick(maus_pos) and (not animation or not animation.aktiv):
                    gewaehlter_modus = "60s"
                    button_60.animiere_click()
                if button_120.klick(maus_pos) and (not animation or not animation.aktiv):
                    gewaehlter_modus = "120s"
                    button_120.animiere_click()

                if button_start.klick(maus_pos) and gewaehlter_modus and (not animation or not animation.aktiv):
                    animation = Animation(MODI[gewaehlter_modus])
                    animation.starten()
                    pausiert = False
                    button_start.animiere_click()

                if button_stop.klick(maus_pos):
                    if animation and animation.aktiv:
                        animation.stoppen()
                        animation = None
                        pausiert = False
                    button_stop.animiere_click()

                if button_pause.klick(maus_pos) and animation and animation.aktiv:
                    if pausiert:
                        animation.fortsetzen()
                        pausiert = False
                    else:
                        animation.pausieren()
                        pausiert = True
                    button_pause.animiere_click()

        fenster.fill(DUNKEL_GRAU)

        if animation and animation.aktiv:
            animation.zeichnen(fenster, breite, hoehe, sterne, zeit)

            rest = int(animation.verbleibende_zeit())
            timer_text = schrift_gross.render(f"{rest} s", True, WEISS)
            fenster.blit(timer_text, (breite // 2 - timer_text.get_width() // 2, 40))

            if gewaehlter_modus:
                modus_text = schrift_klein.render(MODI_NAMEN[gewaehlter_modus], True, GELB)
                fenster.blit(modus_text, (breite // 2 - modus_text.get_width() // 2, 100))

            if pausiert:
                pause_text = schrift_normal.render("PAUSE - P druecken", True, GELB)
                fenster.blit(pause_text, (breite // 2 - pause_text.get_width() // 2, hoehe // 2))

            if animation.ist_fertig():
                animation = None
                pausiert = False
        else:
            for stern in sterne:
                stern.bewegen(0.2, 0.2, breite, hoehe)
                stern.zeichnen(fenster, zeit)

            puls_zeit += 0.008
            puls_radius = int(50 + math.sin(puls_zeit) * 30)
            puls_farbe = int(200 + math.sin(puls_zeit) * 55)
            pygame.draw.circle(fenster, (puls_farbe, puls_farbe, puls_farbe), (breite // 2, hoehe // 2), puls_radius, 4)
            kern_radius = int(15 + math.sin(puls_zeit) * 8)
            pygame.draw.circle(fenster, (255, 255, 255), (breite // 2, hoehe // 2), kern_radius, 2)

            if gewaehlter_modus:
                status_text = schrift_normal.render(f"AUSGEWAEHLT: {MODI_NAMEN[gewaehlter_modus]}", True, GRUEN)
                fenster.blit(status_text, (breite // 2 - status_text.get_width() // 2, hoehe // 2 + 100))
            else:
                status_text = schrift_normal.render("WAHLEN SIE EINEN MODUS (1, 2, 3)", True, GRAU_HELL)
                fenster.blit(status_text, (breite // 2 - status_text.get_width() // 2, hoehe // 2 + 100))

        entwicklung_text = schrift_klein.render("Entwickelt von Safwat Burkhonov", True, GRUEN)
        fenster.blit(entwicklung_text, (breite - entwicklung_text.get_width() - 10, hoehe - 25))

        button_30.zeichnen(fenster, schrift_normal)
        button_60.zeichnen(fenster, schrift_normal)
        button_120.zeichnen(fenster, schrift_normal)
        button_start.zeichnen(fenster, schrift_normal)
        button_stop.zeichnen(fenster, schrift_normal)
        button_pause.zeichnen(fenster, schrift_normal)

        hotkey_text = schrift_klein.render("1=30s 2=60s 3=2min ENTER=START S=STOP P=PAUSE ESC=EXIT", True, GRAU_HELL)
        fenster.blit(hotkey_text, (breite // 2 - hotkey_text.get_width() // 2, hoehe - 55))

        pygame.display.flip()
        uhr.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()