# Concurrency

The conversion of different pages is largely independent, so it makes sense to process them concurrently. Unfortunately, [djvulibre-python](https://github.com/FriedrichFroebel/python-djvulibre) does not support free-threading nor subinterpreters, so the only possibility is to use multiprocessing.

This comes with obvious drawbacks:

1. Processes are more heavyweight than threads and subinterpreters, and the communication between them is not straightforward.
2. DjvuLibre objects are not pickle-able, so we have to read the documents anew from every worker.
3. Logging can get messed up, especially with [Rich](https://github.com/Textualize/rich)'s progress indicator.

We address the first two concerns by using a multiprocessing pool with n workers, where the k-th worker is responsible for pages k, n + k, 2n + k, etc. The number of workers is determined by the reported CPU count.

To address the third concern, we use a special logger in the child processes that passes log messages to the parent instead of trying to print them. We also pass exceptions to the parent, but only after logging them because otherwise their stack trace gets lost. We abort the entire conversion if any of the workers fails.
