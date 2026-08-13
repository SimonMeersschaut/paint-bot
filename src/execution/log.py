import json

class Log:

    @classmethod
    def set_progress(cls, index: int, project_name: str):
        with open("data/progress.json", 'r') as f:
            data = json.load(f)

        data.update({project_name: index})

        with open("data/progress.json", 'w') as f:
            json.dump(data, f)


    @classmethod
    def get_progress(cls, project_name: str) -> int:
        with open("data/progress.json", 'r') as f:
            data = json.load(f)
        return data.get(project_name, 0)
