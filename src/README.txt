Prije početka korištenja same aplikacije potrebno je konfigurisati parametre aplikacije.

Konfiguracioni fajlovi se nalaze u config/ direktorijumu.
Postoje glavna tri konfiguraciona fajla:

credentials.py	-	Kredencijali i parametri

			za Keystone i RabbitMQ servis

config.py	-	Težine za parametre na osnovu kojih se izračunava opterećenje hosta
			Vrijeme nakon koje će se periodično pokretati prikupljanje podataka
			Minimalno vrijeme nakon kojeg će se instanca moći ponovo migrirati
			Parametri za logovanje

test_config.py - Parametri koje koriste skripte za testiranje
		 Image, flavor, zona za instance koje će se pokretati
	         Definišu se hostovi na kojima će se instance pokretati
		 i brisati

Nakon konfigurisanja pokrenuti skriptu balancer_app.py


Za testiranje koriste se sledeće skripte:

"TEST - delete_servers.py" - koristi se za brisanje instanci. Skripti se proslijedjuje
   			     broj instanci koji se briše, inače koristi se default vrijednost
		             definisana u test_config.py

"TEST - start_servers.py" - koristi se za pokretanje instanci. Skripti se proslijeđuje
 			    broj instanci koji se briše, inače koristi se default vrijednost
			    definisana u test_config.py

"TEST - scheduled_start_delete.py" - koristi se za periodično pokretanje i brisanje
				     instanci u cloudu. Vremena pokretanja i hostovi
				     na kojima će se instance pokretati i brisati su
			   	     definisani u test_config.py

logs/	-	default direktorijum za log fajlove


parse_log.py - pomoćna skripta za parsiranje log fajlova i prikaz statističkih podataka
	       Podaci se prikazuju na graficima.


POTREBNE BIBLIOTEKE:
	python-novaclient     - Klijent za Openstack Nova compute servis
	python-keystoneclient -	Klijent za Openstack Keystone servis
	pika		      - Koristi se za rad sa RabbitMQ servisom
	matplotlib	      - Koristi se za iscrtavanje grafika.
				Za rad ove biblioteke potrebni su još sledeći
				moduli:
		  		  - numpy
				  - dateutil
				  - pytz
				  - six


************************************
Author: Aleksandar Vukotić

Elektrotehnički fakultet, Banja Luka
