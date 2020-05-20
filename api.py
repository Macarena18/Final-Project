from src.config import PORT
from src.app import app
import src.controllers.recommend
import src.controllers.get
import src.controllers.collaborativefiltering
import src.controllers.predictions


app.run("0.0.0.0", PORT, debug=True)