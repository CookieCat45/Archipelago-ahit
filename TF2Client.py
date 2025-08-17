from worlds.tf2.Client import launch
import Utils
import ModuleUpdate
ModuleUpdate.update()

if __name__ == "__main__":
    Utils.init_logging("TF2Client", exception_logger="Client")
    launch()
