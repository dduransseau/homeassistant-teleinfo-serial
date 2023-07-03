
class StatusRegisterParser:

    POSITION_CONTACT_SEC_POSITION = (0,)
    POSITION_ORGANE_COUPURE = (1, 4)
    POSITION_CACHE_BORNE_DISTRI = (4,)
    POSITION_SURTENSION = (6,)
    POSITION_DEPASEMENT_PUISSANCE = (7,)
    POSITION_FONCTIONNEMENT8PROD_CONSO = (8,)
    POSITION_SENS_ENERGIE_ACTIVE = (9,)
    POSITION_TARIF_FOURN = (10,14)
    POSITION_TARIF_DISTRI = (14,16)
    POSITION_HORLOGE_DEGRADE = (16,)
    POSITION_MODE_TELEINFO = (17,)
    POSITION_SORTIE_COM_EURIDIS = (19,21)
    POSITION_STATUS_CPL = (21,23)
    POSITION_SYNCHRO_CPL = (23,)
    POSITION_COULEUR_JOUR = (24,26)
    POSITION_COULEUR_DEMAIN = (26,28)
    POSITION_PREAVIS_PM = (28,30)
    POSITION_PM = (30,32)


    def __init__(self, status_str="") -> None:
        self._str = status_str
        self._bits_str = ""
        if status_str:
            self.parse_str(status_str)


    @staticmethod
    def parse_value(position, str):
        try:
            if len(position) == 1:
                val =str[position[0]]
            else:
                val = str[position[0]:position[1]]
            return int(val, 2)
        except ValueError:
            pass

    @staticmethod
    def register_value(position):
        def decorator(func):
            @property
            def wrapper(self):
                return self.parse_value(position, self._bits_str)
            return wrapper
        return decorator

    @register_value(POSITION_ORGANE_COUPURE)
    def organe_coupure(self):
        return self._bits_str
        
    @register_value(POSITION_CONTACT_SEC_POSITION)
    def contact_sec(self):
        return self._bits_str
    
    @register_value(POSITION_CACHE_BORNE_DISTRI)
    def cache_borne_distri(self):
        return self._bits_str
    
    @register_value(POSITION_SURTENSION)
    def surtension(self):
        return self._bits_str
    
    @register_value(POSITION_DEPASEMENT_PUISSANCE)
    def depassement_puissance(self):
        return self._bits_str
    
    @register_value(POSITION_FONCTIONNEMENT8PROD_CONSO)
    def fonctionnement_prod_conso(self):
        return self._bits_str
    
    @register_value(POSITION_SENS_ENERGIE_ACTIVE)
    def sens_energie_active(self):
        return self._bits_str
    
    @register_value(POSITION_TARIF_FOURN)
    def tarif_fourn(self):
        return self._bits_str
    
    @register_value(POSITION_TARIF_DISTRI)
    def tarif_distri(self):
        return self._bits_str

    @register_value(POSITION_HORLOGE_DEGRADE)
    def horloge_degrade(self):
        return self._bits_str

    @register_value(POSITION_MODE_TELEINFO)
    def mode_teleinfo(self):
        return self._bits_str

    @register_value(POSITION_SORTIE_COM_EURIDIS)
    def sortie_com_euridis(self):
        return self._bits_str

    @register_value(POSITION_STATUS_CPL)
    def status_cpl(self):
        return self._bits_str

    @register_value(POSITION_SYNCHRO_CPL)
    def synchro_cpl(self):
        return self._bits_str

    @register_value(POSITION_COULEUR_JOUR)
    def couleur_jour(self):
        return self._bits_str

    @register_value(POSITION_COULEUR_DEMAIN)
    def couleur_demain(self):
        return self._bits_str

    @register_value(POSITION_PREAVIS_PM)
    def preavis_pm(self):
        return self._bits_str

    @register_value(POSITION_PM)
    def pm(self):
        return self._bits_str

    def parse_str(self, s):
        self._str = s
        binary_string = ""
        for char in self._str:
            binary_string += bin(int(char,16))[2:].zfill(4)
        s = binary_string[::-1] # Reverse the binary string order to map bits as listed in documentation
        self._bits_str = s



if __name__ == "__main__":

    STGE = "00DA0001"
    parser = StatusRegisterParser()
    parser.parse_str(STGE)

    print("Contact sec", parser.contact_sec)
    print("Organe coupure", parser.organe_coupure)
    print("Cache distri", parser.cache_borne_distri)
    print("Sortie euridi", parser.sortie_com_euridis)
    print("Mode teleinfo", parser.mode_teleinfo)
    print("Status CPL", parser.status_cpl)
    print("Synchro CPL", parser.synchro_cpl)
    print("Couleur du jour", parser.couleur_jour)
    print("Couleur du lendemain", parser.couleur_demain)
    print("Preavis PM", parser.preavis_pm)
    print("PM", parser.pm)