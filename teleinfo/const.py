from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfEnergy, UnitOfPower, UnitOfApparentPower
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorEntity,
    SensorStateClass
)

DOMAIN = "teleinfo"

class TeleinfoProtocolType:
    HISTORIQUE = "historique"
    STANDARD = "standard"

class TeleinfoMetricBase:

	def __init__(self, key, metric_type=int, length=9, timestamp=False, description=""):
		self.key = key
		self.metric_type = metric_type
		self.length = length
		self.has_timestamp = timestamp
		self.description = description
		self._season = None
		self._timestamp = None

class TeleinfoIndex(TeleinfoMetricBase):
	_attr_device_class = SensorDeviceClass.ENERGY
	_attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
	_attr_state_class = SensorStateClass.TOTAL_INCREASING

class TeleinfoVoltageMetric(TeleinfoMetricBase):
	_attr_device_class = SensorDeviceClass.ENERGY
	_attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
	_attr_state_class = SensorStateClass.MEASUREMENT

class TeleinfoApparentPowerMetric(TeleinfoMetricBase):
	_attr_device_class = SensorDeviceClass.ENERGY
	_attr_native_unit_of_measurement = UnitOfApparentPower.VOLT_AMPERE
	_attr_state_class = SensorStateClass.MEASUREMENT

class TeleinfoPowerMetric(TeleinfoMetricBase):
	_attr_device_class = SensorDeviceClass.ENERGY
	_attr_native_unit_of_measurement = UnitOfPower.WATT
	_attr_state_class = SensorStateClass.MEASUREMENT

class TeleinfoAmpereMetric(TeleinfoMetricBase):
	_attr_device_class = SensorDeviceClass.ENERGY
	_attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
	_attr_state_class = SensorStateClass.MEASUREMENT


TELEINFO_KEY = {
	"ADSC": { "metric_length": 12, "content_type": str, "description": "Adresse Secondaire du Compteur", "label": "adresseSecondaire"},
	"VTIC": { "metric_length": 2, "content_type": int, "description": "Version de la TIC", "label": "versionTIC" },
	"DATE": { "metric_length": 0, "content_type": str, "description": "Date et heure courante", "label": "datetime", "timestamp": True },
	"NGTF": {"metric_length": 16, "content_type": str, "description": "Nom du calendrier tarifaire fournisseur", "label": "nomCalendrierFournisseur"},
	"LTARF": {"metric_length": 16, "content_type": str, "description": "Libellé tarif fournisseur en cours", "label": "labelTarifFournisseur"},
	"EAST": { "metric_length": 9, 
          "content_type": int, 
          "description": "Energie active soutirée totale", 
          "label": "energieActiveSoutireeTotale",
		  "class": TeleinfoIndex},
	"EASF01": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 01", "class": TeleinfoIndex },
	"EASF02": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 02", "class": TeleinfoIndex },
	"EASF03": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 03", "class": TeleinfoIndex },
	"EASF04": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 04", "class": TeleinfoIndex },
	"EASF05": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 05", "class": TeleinfoIndex },
	"EASF06": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 06", "class": TeleinfoIndex },
	"EASF07": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 07", "class": TeleinfoIndex },
	"EASF08": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 08", "class": TeleinfoIndex },
	"EASF09": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 09", "class": TeleinfoIndex },
	"EASF10": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Fournisseur, index 10", "class": TeleinfoIndex },
	
	"EASD01": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Distributeur, index 01", "class": TeleinfoIndex },
	"EASD02": { "metric_length": 9,  "content_type": int, "description": "Energie active soutirée Distributeur, index 02", "class": TeleinfoIndex },
	"EASD03": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Distributeur, index 03", "class": TeleinfoIndex },
	"EASD04": { "metric_length": 9, "content_type": int, "description": "Energie active soutirée Distributeur, index 04", "class": TeleinfoIndex },

    "IRMS1": { "metric_length": 3, "content_type": int, "description": "Courant efficace, phase 1 ", "class": TeleinfoAmpereMetric },
    "URMS1": { "metric_length": 3, "content_type": int, "description": "Tension efficace, phase 1 ", "class": TeleinfoVoltageMetric },
    "SINST1": { "metric_length": 5, "content_type": int, "description": "Puissance app. Instantanée soutirée phase 1", "class": TeleinfoApparentPowerMetric },
    "SMAXN": { "metric_length": 5, "content_type": int, "description": "Puissance app. max. soutirée n", "class": TeleinfoApparentPowerMetric, "timestamp": True },
    "SMAXN-1": { "metric_length": 5, "content_type": int, "description": "Puissance app. max. soutirée n-1", "class": TeleinfoApparentPowerMetric, "timestamp": True },
	
	"PREF": { "metric_length": 2, "content_type": int, "description": "Puissance app. de référence", "unit": "kVA" },
	"PCOUP": { "metric_length": 2, "content_type": int, "description": "Puissance app. de coupure", "unit": "kVA" },
	"SINSTS": { "metric_length": 5, "content_type": int, "description": "Puissance app. Instantanée soutirée", "class": TeleinfoApparentPowerMetric },
	"SMAXSN": { "metric_length": 5, "content_type": int, "description": "Puissance app. max. soutirée n", "class": TeleinfoApparentPowerMetric, "timestamp": True },
	"SMAXSN-1": { "metric_length": 5, "content_type": int, "description": "Puissance app. max. soutirée n-1", "class": TeleinfoApparentPowerMetric, "timestamp": True },
	"CCASN": { "metric_length": 5, "content_type": int, "description": "Point n de la courbe de charge active soutirée", "class": TeleinfoPowerMetric, "timestamp": True },
	"CCASN-1": { "metric_length": 5, "content_type": int, "description": "Point n-1 de la courbe de charge active soutirée", "class": TeleinfoPowerMetric, "timestamp": True },
	"UMOY1": { "metric_length": 3, "content_type": int, "description": "Tension moy. ph. 1", "class": TeleinfoVoltageMetric, "timestamp": True },
	
	"STGE": { "metric_length": 8, "content_type": str, "description": "Registre de Statuts"},
	"DPM1": { "metric_length": 2, "content_type": int, "description": "Début Pointe Mobile 1", "timestamp": True },
	"FPM1": { "metric_length": 2, "content_type": int, "description": "Fin Pointe Mobile 1", "timestamp": True },
	"DPM2": { "metric_length": 2, "content_type": int, "description": "Début Pointe Mobile 2", "timestamp": True },
	"FPM2": { "metric_length": 2, "content_type": int, "description": "Fin Pointe Mobile 2", "timestamp": True },
	"DPM3": { "metric_length": 2, "content_type": int, "description": "Début Pointe Mobile 3", "timestamp": True },
	"FPM3": { "metric_length": 2, "content_type": int, "description": "Fin Pointe Mobile 3", "timestamp": True },
	
	"MSG1": { "metric_length": 32, "content_type": str, "description": "Message court "},
	"MSG2": { "metric_length": 16, "content_type": str, "description": "Message Ultra court"},
	"PRM": { "metric_length": 14, "content_type": str, "description": "PRM"},
	"RELAIS": { "metric_length": 3, "content_type": str, "description": "Relais"},
	"NTARF": { "metric_length": 2, "content_type": str, "description": "Numéro de l'index tarifaire en cours "},
	"NJOURF": { "metric_length": 2, "content_type": str, "description": "Numéro du jour en cours calendrier fournisseur"},
	"NJOURF+1": { "metric_length": 2, "content_type": str, "description": "Numéro du prochain jour calendrier fournisseur "},
	"PJOURF+1": { "metric_length": 98, "content_type": str, "description": "Profil du prochain jour calendrier fournisseur"},
	"PPOINTE": { "metric_length": 98, "content_type": str, "description": "Profil du prochain jour de pointe"}
}

TELEINFO_STEG1 = {
	0: "fermé",
	1: "ouvert"
}

TELEINFO_STEG2 = {
	0: "fermé",
	1: "ouvert sur surpuissance",
	2: "ouvert sur surtension",
	3: "ouvert sur délestage",
	4: "ouvert sur ordre CPL ou Euridis",
	5: "ouvert sur une surchauffe avec une valeur du courant supérieure au courant de commutation maximal",
	6: "ouvert sur une surchauffe avec une valeur de courant inférieure au courant de commutation maximal",
}

TELEINFO_STEG3 = {
	0: "pas de surtension",
	1: "surtension"
}

TELEINFO_STEG4 = {
	0: "pas de dépassement",
	1: "dépassement en cours"
}

TELEINFO_STEG5 = {
	0: "consommateur",
	1: "producteur"
}

TELEINFO_STEG6 = {
	0: "énergie active positive",
	1: "énergie active négative"
}

TELEINFO_STEG7 = {
	0: "énergie ventilée sur Index 1",
	1: "énergie ventilée sur Index 2",
	2: "énergie ventilée sur Index 3",
	3: "énergie ventilée sur Index 4",
	4: "énergie ventilée sur Index 5",
	5: "énergie ventilée sur Index 6",
	6: "énergie ventilée sur Index 7",
	7: "énergie ventilée sur Index 8",
	8: "énergie ventilée sur Index 9",
	9: "énergie ventilée sur Index 10",
}

TELEINFO_STEG8 = {
	0: "horloge correcte",
	1: " horloge dégradée"
}

TELEINFO_STEG9 = {
	0: "mode historique",
	1: "mode standard"
}

TELEINFO_STEG10 = {
	0: "désactivée",
	1: "activée sans sécurité",
	3: "activée avec sécurité"
}

TELEINFO_STEG11 = {
	0: "New/Unlock",
	1: "New/Lock",
	3: "Registered"
}

TELEINFO_STEG12 = {
	0: "non synchronisé",
	1: "synchronisé"
}

TELEINFO_STEG13 = {
	0: "pas d'annonce",
	1: "Bleu",
	2: "Blanc",
	3: "Rouge"
}

TELEINFO_STEG14 = {
	0: "pas de préavis en cours",
	1: "préavis PM1 en cours",
	2: "préavis PM2 en cours",
	3: "préavis PM3 en cours"
}

TELEINFO_STEG15 = {
	0: "Pas de pointe mobile",
	1: "PM 1 en cours",
	2: "PM 2 en cours",
	3: "PM 3 en cours"
}

TELEINFO_STATUS_REGISTER = {
	"contact_sec": TELEINFO_STEG1,
	"organe_coupure": TELEINFO_STEG2,
	"cache_borne_distri": TELEINFO_STEG1,
	"surtension": TELEINFO_STEG3,
	"depassement_puissance": TELEINFO_STEG4,
	"fonctionnement_prod_conso": TELEINFO_STEG5,
	"sens_energie_active": TELEINFO_STEG6,
	"tarif_fourn": TELEINFO_STEG7,
	"tarif_distri": TELEINFO_STEG7,
	"horloge_degrade": TELEINFO_STEG8,
	"mode_teleinfo": TELEINFO_STEG9,
	"sortie_com_euridis": TELEINFO_STEG10,
	"status_cpl": TELEINFO_STEG11,
	"synchro_cpl": TELEINFO_STEG12,
	"couleur_jour": TELEINFO_STEG13,
	"couleur_demain": TELEINFO_STEG13,
	"preavis_pm": TELEINFO_STEG14,
	"pm": TELEINFO_STEG15
}



EURIDIS_MANUFACTURER = {'01': 'CROUZET / MONETEL',
 '02': 'SAGEM / SAGEMCOM',
 '03': 'SCHLUMBERGER / ACTARIS / ITRON',
 '04': 'LANDIS ET GYR / SIEMENS METERING / LANDIS+GYR',
 '05': 'SAUTER / STEPPER ENERGIE France / ZELLWEGER',
 '06': 'ITRON',
 '07': 'MAEC',
 '08': 'MATRA-CHAUVIN ARNOUX / ENERDIS',
 '09': 'FAURE-HERMAN',
 '10': 'SEVME / SIS',
 '11': 'MAGNOL / ELSTER / HONEYWELL',
 '12': 'GAZ THERMIQUE',
 '14': 'GHIELMETTI / DIALOG E.S. / MICRONIQUE',
 '15': 'MECELEC',
 '16': 'LEGRAND / BACO',
 '17': 'SERD-SCHLUMBERGER',
 '18': 'SCHNEIDER / MERLIN GERIN / GARDY',
 '19': 'GENERAL ELECTRIC / POWER CONTROL / ABB',
 '20': 'NUOVO PIGNONE / DRESSER',
 '21': 'SCLE',
 '22': 'EDF',
 '23': 'GDF / GDF-SUEZ',
 '24': 'HAGER - GENERAL ELECTRIC',
 '25': 'DELTA-DORE',
 '26': 'RIZ',
 '27': 'ISKRAEMECO',
 '28': 'GMT',
 '29': 'ANALOG DEVICE',
 '30': 'MICHAUD',
 '31': 'HEXING ELECTRICAL CO. Ltd',
 '32': 'SIAME',
 '33': 'LARSEN & TOUBRO Limited',
 '34': 'ELSTER / HONEYWELL',
 '35': 'ELECTRONIC AFZAR AZMA',
 '36': 'ADVANCED ELECTRONIC COMPAGNY Ldt',
 '37': 'AEM',
 '38': 'ZHEJIANG CHINT INSTRUMENT & METER CO. Ldt',
 '39': 'ZIV',
 '70': 'LANDIS et GYR (export ou régie)',
 '71': 'STEPPER ENERGIE France (export ou régie)',
 '81': 'SAGEM / SAGEMCOM',
 '82': 'LANDIS ET GYR / SIEMENS METERING / LANDIS+GYR',
 '83': 'ELSTER / HONEYWELL',
 '84': 'SAGEM / SAGEMCOM',
 '85': 'ITRON'}

EURIDIS_DEVICE = {'01': 'Compteur bleu monophasé multitarif électronique (BBR) - 1ère génération', 
			'02': 'Centrale de mesure G3 - Poste HTA/BT', 
			'03': 'Concentrateur multi-compteurs / électrique + 2 fluides', 
			'04': 'Concentrateur simplifié / élec', 
			'05': 'Compteur bleu monophasé simple tarif électronique - 1ère génération', 
			'06': 'Compteur jaune électronique / tarif modulable', 
			'07': 'Compteur électronique universel (PRISME ou ICE)', 
			'08': 'Compteur sauter modifié EURIDIS', 
			'09': 'Compteur bleu triphasé électronique - 1ère génération', 
			'10': 'Compteur jaune électronique 2ème génération', 
			'11': 'Compteur bleu monophasé simple tarif FERRARIS', 
			'12': 'Compteur prisme', 
			'13': 'Centrale de mesure G1 - Poste HTA/BT', 
			'14': 'Analyseur de courbe de charge (panel BT)', 
			'15': 'Compteur bleu monophasé multitarif électronique sans BBR', 
			'16': 'Compteur bleu expérimentation « 10000 ICC »', 
			'17': 'ICC expérimentation « 10000 ICC »', 
			'18': 'Détecteur de défauts / HTA ', 
			'19': 'Concentrateur multi-compteurs / 3 fluides indifférenciés', 
			'20': 'Compteur bleu monophasé multitarif ½ taux - 1ère génération', 
			'21': 'Compteur bleu triphasé ½ taux - 1ére génération', 
			'22': 'Compteur bleu monophasé multitarif - 2ème génération', 
			'23': 'Compteur bleu monophasé multitarif ½ taux - 2ème génération', 
			'25': 'Compteur bleu monophasé simple tarif - 2ème génération', 
			'26': 'Compteur bleu triphasé - palier 2000 - 2ème génération', 
			'27': 'Compteur bleu triphasé - palier 2000 1?2 taux - 2ème génération', 
			'28': 'Compteur bleu monophasé multitarif - palier 2007 - 3ème génération', 
			'29': 'Compteur bleu monophasé multitarif ½ taux - palier 2007 - 3ème génération', '30': 'Compteur bleu triphasé - palier 2007 - 3ème génération',
			'31': 'Compteur bleu triphasé ½ taux - palier 2007 - 3ème génération',
			'32': 'Compteur bleu triphasé télétotalisation',
			'33': 'Compteur jaune électronique branchement direct',
			'34': 'Compteur ICE 4 quadrants',
			'35': 'Compteur trimaran 2P classe 0',
			'36': 'Compteur PME-PMI BT > 36kva',
			'37': 'Compteur prépaiement',
			'38': 'Compteur triphasé HXE34 de HECL',
			'40': "Système d'affichage multiusage (SAM)",
			'42': 'Compteur monophasé export (ACTARIS)',
			'43': 'Compteur monophasé export (ACTARIS)',
			'44': 'Compteur triphasé export ACTARIS',
			'46': 'Modem EURIDIS pour compteur PME-PMI',
			'52': 'Concentrateur simplifié / gaz ou Transpondeur Gaz EURIDIS',
			'53': 'Concentrateur multi-compteurs / VGR',
			'54': 'Concentrateur multi-compteurs / gaz',
			'58': 'Baie prisme de télétotalisation (1 exemplaire à ce jour) expérimentation Lyon',
			'60': 'Compteur monophasé 60A LINKY - généralisation G1 - arrivée basse',
			'61': 'Compteur monophasé 60A LINKY - généralisation G3 - arrivée haute',
			'62': 'Compteur monophasé 90A LINKY - généralisation G1 - arrivée basse',
			'63': 'Compteur triphasé 60A LINKY - généralisation G1 - arrivée basse',
			'64': 'Compteur monophasé 60A LINKY - généralisation G3 - arrivée  basse',
			'65': 'Compteur monophasé 90A LINKY expérimentation CPL G3 (2000 ex.)',
			'66': 'Module du compteur modulaire généralisation',
			'68': 'Compteur triphasé 60A LINKY - pilote G1 - arrivée basse',
			'70': 'Compteur monophasé 60A LINKY - interopérabilité G3 - arrivée basse',
			'71': 'Compteur triphasé 60A LINKY - interopérabilité G3 - arrivée basse',
			'72': 'Compteur monophasé HXE12K 10-80A 4 tarifs (Hexing Electrical co',
			'74': 'Compteur triphasé HXE34K 230/400V 10-80A 4 tarifs (Hexing Electrical co',
			'75': 'Compteur monophasé 90A LINKY - palier 1 G3 - arrivée basse',
			'76': 'Compteur triphasé 60A LINKY - palier 1 G3 - arrivée basse',
			'86': 'Compteur numérique SEI monophasé 60A 230V - G3 - arrivée basse - 60Hz',
			'87': 'Compteur numérique SEI triphasé 60A 230/400V - G3 - 60Hz',
			'88': 'Compteur monophasé PLC DSMR2.2 (Actaris)',
			'89': 'Compteur triphasé PLC DSMR2.2 (Actaris)',
			'90': 'Compteur monophasé CPL intégré 1ère génération',
			'91': 'Compteur triphasé CPL intégré 2ème génération',
			'92': 'Compteur monophasé 90A LINKY ORES - G3 Palier 1',
			'93': 'Compteur triphasé 60A 3 fils LINKY ORES - G3 Palier 1',
			'94': 'Compteur triphasé 60A 4 fils LINKY ORES - G3 Palier 1',
			'98': 'BCPL  G0 pour compteur CJE et CBE',
			'AA': 'Coupleur EURIDIS bluetooth (PKE)',
			'DC': 'BCPL G1 LINKY pour compteur CJE',
			'45': 'Compteur triphasé AECL',
			'67': 'Module du compteur modulaire expérimentation (non déployé)'}