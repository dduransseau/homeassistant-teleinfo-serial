
from .utils import StatusRegisterParser

def get_bit_value(ascii_value, bit_position):
        # Décaler la valeur entière à droite pour aligner le bit souhaité à la position 0
    shifted_value = ascii_value >> bit_position

    # Masquer les bits non souhaités en effectuant un AND logique avec 1
    bit_value = shifted_value & 1

    return bit_value


def get_bits_range_value(ascii_value, start_position, end_position):
    # Décaler la valeur entière à droite pour aligner le début de la plage à la position 0
    shifted_value = ascii_value >> start_position

    # Calculer le nombre de bits dans la plage spécifiée
    num_bits = end_position - start_position + 1

    # Masquer les bits non souhaités en effectuant un AND logique avec une valeur appropriée
    bit_value = shifted_value & ((1 << num_bits) - 1)

    return bit_value


def parse_linky_status(status_str):
    status_int = int(status_str, 16)
    status_bits_str = format(status_int, 'b')
    print(status_bits_str)
    # Reverse order of tits string
    s = status_bits_str[::-1]
    print(s)
    contact_sec = s[0]
    organe_coupure = s[1:4]
    cache_borne_distri = s[4]
    surtension = s[6]
    depassement_puissance = s[7]
    fonctionnement_prod_conso = s[8]
    sens_energie_active = s[9]
    tarif_fourn = s[10:14]
    tarif_distri = s[14:16]
    horloge_degrade = s[16]
    mode_teleinfo = s[17]
    sortie_com_euridis = s[19:21]
    status_cpl = s[21:23]
    synchro_cpl = s[23]
    couleur_jour = s[24:26]
    couleur_demain = s[26:28]
    preavis_pm = s[28:30]
    pm = s[30:32]
    print(bool(contact_sec), int(organe_coupure, 2), bool(organe_coupure))
    print(cache_borne_distri, surtension, depassement_puissance, fonctionnement_prod_conso,sens_energie_active)
    print(tarif_fourn, tarif_distri, horloge_degrade, mode_teleinfo, sortie_com_euridis)
    print(status_cpl, synchro_cpl, couleur_jour, couleur_demain, preavis_pm, pm)

if __name__ == "__main__":

    STGE = "00DA0001"
    # # Convertir la chaîne ASCII en valeur entière
    # ascii_value = int(STGE, 16)

    #     # Récupérer la valeur du bit 0
    # bit_0_value = get_bit_value(ascii_value, 0)
    # print("Valeur du bit 0 :", bit_0_value)

    # # Récupérer la valeur des bits 1 à 3 (sous forme numérique)
    # bits_1_to_3_value = get_bits_range_value(ascii_value, 1, 3)
    # print("Valeur des bits 1 à 3 :", bits_1_to_3_value)

    # # Récupérer la valeur des bits 4 et 5 (sous forme booléenne)
    # bit_4_value = bool(get_bit_value(ascii_value, 4))
    # bit_5_value = bool(get_bit_value(ascii_value, 5))
    # print("Valeur du bit 4 :", bit_4_value)
    # print("Valeur du bit 5 :", bit_5_value)

    parse_linky_status(STGE)
