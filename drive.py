import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
import logging

CREDENTIAL_FILE = "mycreds.txt"
CHUNK_SIZE = 1024 * 1024 * 256  # 256 MB

class DriveManager():
    def __init__(self):
        self.gauth = GoogleAuth()

    def checkCredentials(self):

        if os.path.isfile(CREDENTIAL_FILE):
            # Se esiste, usa le credenziali salvate sul file
            self.gauth.LoadCredentialsFile(CREDENTIAL_FILE)
            if self.gauth.credentials is None:
                # Se le credenziali non sono valide, autentica l'utente
                self.gauth.LocalWebserverAuth()
                # Salva le nuove credenziali sul file
                self.gauth.SaveCredentialsFile(CREDENTIAL_FILE)
            elif self.gauth.access_token_expired:
                # Se le credenziali sono scadute, aggiornale
                self.gauth.Refresh()
                # Salva le nuove credenziali sul file
                self.gauth.SaveCredentialsFile(CREDENTIAL_FILE)
        else:
            # Se il file delle credenziali non esiste, autentica l'utente e salva le credenziali sul file
            self.gauth = GoogleAuth()
            self.gauth.LocalWebserverAuth()
            self.gauth.SaveCredentialsFile(CREDENTIAL_FILE)

    def uploadFile(self, file_path) -> str:

        logging.info("Uploading file...")

        self.checkCredentials()
       
        service = build('drive', 'v3', credentials=self.gauth.credentials)
        
        file_name = os.path.basename(file_path)
        # Creazione del MediaFileUpload
        file_size = os.path.getsize(file_path)
        media = MediaFileUpload(file_path, chunksize=CHUNK_SIZE, resumable=True)

            # Creazione della richiesta per il caricamento del file
        if file_size > CHUNK_SIZE:
            request = service.files().create(
                body={'name': file_name},
                media_body=media,
                supportsAllDrives=True
            )
            response = None
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        logging.info(f'Progresso: {int(status.progress() * 100)}.')
                except HttpError as error:
                    if error.resp.status in [500, 502, 503, 504]:
                        logging.error('Errore di connessione durante il caricamento. Riprovo...')
                        continue
                    elif error.resp.status == 400 and 'ResumableUploadChunkNotFoundException' in error.content.decode():
                        logging.error('Chunk non trovato. Riprovo...')
                        media.resumable_progress = True
                        continue
                    else:
                        raise
            logging.info(f"Caricamento del file '{file_name}' completato con successo")
        else:
            try:
                file_metadata = {'name': file_name}
                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    supportsAllDrives=True
                ).execute()
                logging.info(f"Caricamento del file '{file_name}' completato con successo")
            except HttpError as error:
                logging.error(f"Errore durante il caricamento del file '{file_name}': {error}")
                
        results = service.files().list(q=f"name='{file_name}' and trashed = false", fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        if len(items) == 0:
            logging.error('Il file non è stato trovato.')
        else:
            file_id = items[0]['id']

        permission = {
        'type': 'anyone',
        'role': 'reader',
        'withLink': True
        }

        res = service.permissions().create(fileId=file_id, body=permission).execute()
        print(res)
        link_nuovo = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        link = f"https://drive.google.com/uc?id={file_id}"
        logging.info(f"Link di condivisione: {link}")
        print(f"Link di condivisione: {link}")
        print(f"Link di condivisione: {link_nuovo}")

        return link
    
print("caicando")
DM = DriveManager()
DM.uploadFile("prova.pdf")
print("caricamento completato")