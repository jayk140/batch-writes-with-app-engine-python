Simple application demonstrating how to execute batch write processing in Google App Engine Python using up-to-date APIs (NDB, Taskqueues). Writes are the most expensive operation in App Engine. For applications with frequently updated entities, for the purpose of keeping a page view count for example, batch wirtes can greatly reduce overall cost. 