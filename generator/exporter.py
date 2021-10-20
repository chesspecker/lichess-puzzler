import pymongo

client = pymongo.MongoClient('<url>')
database = client["chesspecker"]

def get_user(user_id: str):
	collection = database["users"]
	user_object = collection.find_one({"id": user_id})
	return user_object

def create_set(user_object) -> bool:
	newSet = {
		'user': user_object["_id"],
		'puzzles': [],
		'length': 0,
		'bestTime': 0,
	}
	try:
		collection = database["puzzlesets"]
		set_id = collection.insert_one(newSet).inserted_id
		return set_id
	except Exception as err:
		print(err)
		return False

def get_set(game_id: str) -> bool:
	try:
		collection = database["puzzlesets"]
		user_object = get_user(game_id)
		number_of_sets = collection.count_documents({"user": user_object["_id"]})
		if number_of_sets == 0:
			set_id = create_set(user_object)
		else:
			for current_set in collection.find({"user": user_object["_id"]}):
				if current_set["length"] < 30:
					set_id = current_set["_id"]
					break
				else:
					set_id = create_set(user_object)

		return set_id
	except Exception as err:
		print(err)
		return False

def update_game(game_id: str) -> bool:
	try:
		collection = database["games"]
		collection.update_one({"game_id": game_id}, { "$set" : { "analyzed": True }})
		return True
	except Exception as err:
		print(err)
		return False

def insert_puzzle(puzzle, user_id: str) -> bool:
	try:
		collection = database["puzzles"]
		puzzle_id = collection.insert_one(puzzle).inserted_id
		set_id = get_set(user_id)
		collection = database["puzzlesets"]
		collection.update_one({"_id": set_id}, { "$push" : { "puzzles": puzzle_id }})
		collection.update_one({"_id": set_id}, {'$inc': {"length": 1}})
		collection = database["users"]
		collection.update_one({"_id": user_object["_id"]}, {'$inc': {"puzzlesInDb": 1}})
		return True
	except Exception as err:
		print(err)
		return False

def post_puzzle(game_id: str, user_id: str, puzzle) -> None:
		parent = puzzle.node.parent
		assert parent
		json = {
				'game_id': game_id,
				'fen': parent.board().fen(),
				'ply': parent.ply(),
				'moves': [puzzle.node.uci()] + list(map(lambda m : m.uci(), puzzle.moves)),
				'cp': puzzle.cp,
		}
		try:
				insert_puzzle(json, user_id)
		except Exception as e:
				print("Couldn't post puzzle: {}".format(e))