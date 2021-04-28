from ..cache_manager.models import FolderListModel

if __name__ == "__main__":
    root_path = Path().home()
    m = FolderListModel()
    m.root_path = root_path
    print(m.items_as_enum_list)
