# *-* coding: utf-8 *-*

"""
Script che zippa i file contenuti in una cartella che hanno la data di
modifica compresa tra due date; la distanza tra le date usualmente è
pari ad 1 mese

Bisogna impostare manualmente il nome dell'impianto, la cartella con
i dati grezzi e la cartella dove salvare i dati zippati;
il formato di salvataggio dei dati .zip è:
    nome_impianto__data_iniziale__data_finale.zip

Lo script NON elimina i file dalla cartella dei dati grezzi.
"""

import os
import zipfile
from glob import glob
from dateutil.relativedelta import relativedelta
import datetime
import argparse


def convert_date(timestamp):
    """Converte la data di tipo timestamp in data da datetime
    Restituisce la data datetime
    """

    d = datetime.datetime.utcfromtimestamp(timestamp)
    return d


def zip_files(lista_to_zip, nome_impianto, date, dest_folder):
    """Funzione che zippa i files di un timedelta
    Effettua verifiche:
    è già presente lo stesso file?
    ci sono file da zippare?
    """
    
    # zip dei files
    zip_name = ('{}__{}.zip'.format(nome_impianto, date))
    print('Zippando {}'.format(zip_name))

    # nel caso in cui lo zip sia già presente, lo salta
    if zip_name in os.listdir(dest_folder):
        print('{} già presente'. format(zip_name))
        return

    # nel caso in cui non ci siano file da zippare
    if lista_to_zip == []:
        print('Nessun file da zippare in {}'.format(zip_name))
        return

    with zipfile.ZipFile(os.path.join(dest_folder, zip_name), 'w',
                         compression=zipfile.ZIP_DEFLATED) as new_z:

        for file_to_zip in lista_to_zip:
            new_z.write(os.path.basename(file_to_zip))

        print('Zippaggio terminato {}'.format(date))
        print('------------')


# ---------------------------

# creazione del parser
parser = argparse.ArgumentParser(
    description="Zip files dell'impianto dalla orig-folder alla dest-folder")
# definizione argomenti parser
parser.add_argument(
    'Nome_impianto', metavar='nome', type=str,
    help="Nome dell'impianto")
parser.add_argument(
    'Cartella_di_origine', metavar='orig-folder', type=str,
    help='Cartella di origine dei .csv')
parser.add_argument(
    'Cartella_di_destinazione', metavar='dest-folder', type=str,
    help='Cartella di destinazione dei .zip')
parser.add_argument(
    'Data_di_inizio', metavar='begin-date', type=str,
    help='Anno, mese e giorno da cui partire per il salvataggio dei dati')
parser.add_argument(
    'Data_di_fine', metavar='end-date', type=str,
    help='Anno, mese e giorno in cui terminare il salvataggio dei dati')
# esecuzione del parser
args = parser.parse_args()

# cartella contenente i file da zippare
folder = args.Cartella_di_origine
os.chdir(folder)
# cartella dove i file zippati saranno spostati
dest_folder = args.Cartella_di_destinazione
# nome dell'impianto
nome_impianto = args.Nome_impianto
# data iniziale
data_iniziale = args.Data_di_inizio
# data finale
data_finale = args.Data_di_fine
print(nome_impianto + '\n------------\n')


# dizionario contenente la lista dei file da zippare per ogni timedelta
to_zip_all = dict()
to_zip_timedelta = list()

# momento iniziale e finale per cui si vuole zippare i file
FIRST_DATE = datetime.datetime(
    int(data_iniziale[0:4]), int(data_iniziale[4:6]),
    int(data_iniziale[6:8]),
    00, 00, 00)

LAST_DATE = datetime.datetime(
    int(data_finale[0:4]), int(data_finale[4:6]),
    int(data_finale[6:8]),
    23, 59, 59)

# delta di tempo
TIME_DELTA = relativedelta(months=1)

correzione_fuso_orario = datetime.timedelta(hours=2)

# data iniziale
start_date = FIRST_DATE
end_date = start_date + TIME_DELTA

# ciclo per raccogliere tutti i file contenuti in ogni TIME_DELTA
while start_date < LAST_DATE:

    for file_csv in glob('{}\*.csv'.format(folder)):

        data_file = (convert_date(os.path.getmtime(file_csv))
                     + correzione_fuso_orario)
#        print(data_file)
#        print(end_date)

        if start_date <= data_file < end_date:
            # print(file_csv)
            # print(data_file)
            to_zip_timedelta.append(file_csv)

    # salvataggio della lista dei file da zippare per tale mese
    to_zip_all['{}__{}'.format(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d'))
        ] = to_zip_timedelta

    # aggiornamento della data di partenza
    print('{} - {} dati acquisiti, {} elementi'
          .format(start_date, end_date, len(to_zip_timedelta)))

    # reinizializzazione lista file da zippare nel timedelta
    to_zip_timedelta = list()

    # aggiornamento delle date
    start_date = end_date
    end_date += TIME_DELTA

print('Oltre la data ultima')
print('\n'.join(['Start: {}'.format(start_date),
                 'End: {}'.format(LAST_DATE)]))


# zippaggio dei files
for date, lista_to_zip in to_zip_all.iteritems():

    zip_files(lista_to_zip, nome_impianto, date, dest_folder)

    for file_to_delete in lista_to_zip:
        os.remove(file_to_delete)

### informazioni per ogni file contenente in ogni file .zip
##for file_name in glob('{}\*.zip'.format(dest_folder)):
##    with zipfile.ZipFile(file_name, 'r') as zip:
##        for info in zip.infolist():
##            print(info.filename)
##            print('\tModified:\t' + str(datetime.datetime(*info.date_time)))
##            print('\tSystem:\t\t' + str(info.create_system) +
# '(0 = Windows, 3 = Unix)')
##            print('\tZIP version:\t' + str(info.create_version))
##            print('\tCompressed:\t' + str(info.compress_size) + ' bytes')
##            print('\tUncompressed:\t' + str(info.file_size) + ' bytes')
