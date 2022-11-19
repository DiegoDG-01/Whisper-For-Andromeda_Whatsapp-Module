import Log
import whisper
from json import load
from os import getcwd, listdir, chdir, remove
from time import sleep
from pathlib import Path
from pydub import AudioSegment

class Whisper:

    # Function to configure the help function and prepare it for use
    def __init__(self):
        self.Argument = None
        self.Communicate = None
        self.commandsFile = None
        self.AdditionalArgs = None
        self.NameModule = "/whisper"

        self.log = Log.Generate()
        self.model = whisper.load_model("base")

        self.BasePath = getcwd()
        PathModuleMessage = Path(self.BasePath + "/Data/Modules/Messages/Whisper.json")

        self.WhisperMessages = self.__Load_MultiLanguage(PathModuleMessage)


    def requirements(self):

        requeriments = {
            'CommandExecution': "/whisper",
            'ExternalModules': [
                'commandsFile', 'Communicate', 'InterfaceController'
            ],
        }

        return requeriments

    def set_Communicate(self, Communicate):
        self.Communicate = Communicate

    def set_commandFile(self, commandsFile):
        self.commandsFile = commandsFile

    def set_InterfaceController(self, InterfaceControl):
        try:
            self.InterfaceControl = InterfaceControl
        except Exception as error:
            self.log.Write("Configure.py | InterfaceControl # " + str(error))

    def __Load_MultiLanguage(self, Path):
        try:
            with open(Path, 'r') as file:
                file = load(file)
                default_code = file['lang']['default']
                language_code = file['lang'][default_code]['locale']
                return file['messages'][language_code]
        except Exception as error:
            self.log.Write("Whisper.py | Load MultiLanguage # " + str(error))
            return False

    def __PrepareArgs(self, args, additionalArgs):
        if args in self.commandsFile['Active'][self.NameModule]['Args'][0].keys():
            self.Argument = args

            if additionalArgs is not None:
                self.AdditionalArgs = additionalArgs

            return True
        else:
            return False

    # This function is used to initialize the help function
    def EntryPoint(self, args=None, additionalArgs=None):
        # if args is empty or None execute default function else execute different function depending on the args
        if args is None:
            return self.Default()
        else:
            # check if args exist and is a valid argument
            if self.__PrepareArgs(args, additionalArgs):
                # Execute the function in charge of managing the help function
                return self.CommandManager()
            else:
                return False

    # This function is used to function to management of the help functions and execute the correct function
    def CommandManager(self):

        if self.Argument == '-d':
            return self.DescribeCommand()
        elif self.Argument == '-l':
            return self.ListArgs()
        elif self.Argument == '-transcribe':
            return self.Transcribe()
        else:
            return False

    # This function is used to function default or if no argument is given
    def Default(self):
        return self.DescribeCommand()

    def DescribeCommand(self):
        return self.commandsFile['Active'][self.NameModule]['Desc']

    def ListArgs(self):

        List = self.commandsFile['Active'][self.NameModule]['Args'][0]

        ListToMessage = [key + ': ' + List[key] for key in List.keys()]

        return ListToMessage

    def Translate_To_English(self):

        self.Communicate.WriteMessage("# Please send the audio to translate to english")
        self.Communicate.SendMessage()

    def Transcribe(self):

        Name_Audio = "audio.wav"
        PathDownload = str(Path(self.BasePath + "/Data/WhatsApp/Downloads/"))

        self.Communicate.WriteMessage(self.WhisperMessages['info']['send_audio'])
        self.Communicate.SendMessage()

        try:
            while True:
                response = self.Communicate.ReadMediaResponse('_3ojyC')

                # Use function to validate
                if response is not False:
                    if not self.InterfaceControl.download_files():
                        return ["", self.WhisperMessages['error']['download']]
                    else:
                        break

                sleep(0.1)

            sleep(0.2)

            chdir(PathDownload)
            last_download = sorted(listdir(PathDownload), key=lambda x: Path(x).stat().st_mtime)[-1]
            chdir(self.BasePath)

            path_audio = str(Path(PathDownload + '/' + last_download))

            ogg_version = AudioSegment.from_ogg(path_audio)
            ogg_version.export(str(Path(PathDownload + '/' + Name_Audio)), format="wav")

            self.Communicate.WriteMessage(self.WhisperMessages['info']['analyzing'])
            self.Communicate.SendMessage()

            result = self.model.transcribe(str(Path(PathDownload + '/' + Name_Audio)), fp16=False)

            self.Communicate.WriteMessage(self.WhisperMessages['success']['transcription'])
            self.Communicate.SendMessage()

            return ["", '>> '+result["text"]]

        except Exception as error:
            self.log.Write("Whisper.py | Transcribe # " + str(error))
            return ["", self.WhisperMessages['error']['transcription']]
        finally:
            remove(str(Path(PathDownload + '/' + Name_Audio)))
            remove(str(Path(PathDownload + '/' + last_download)))