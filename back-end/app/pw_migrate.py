import models
from peewee_migrate import Router

models.db.connect()

router = Router(models.db,ignore=['PaginatedAPIMixin', 'BaseModel'])

router.create(auto=models)
router.run()

models.db.close()