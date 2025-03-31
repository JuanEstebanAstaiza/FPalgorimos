class SortingAlgorithms:
    def __init__(self):
        pass

    def _get_effective_key(self, key, search_value):
        """
        Retorna una función clave que, si search_value se proporciona,
        genera una tupla (prioridad, valor) donde prioridad es 0 si el string
        del valor contiene search_value, y 1 en caso contrario.
        """
        if search_value is None:
            return key
        else:
            search_str = str(search_value)

            def new_key(x):
                k = key(x)
                # Convertir k a cadena para permitir la búsqueda
                k_str = str(k)
                priority = 0 if search_str in k_str else 1
                return (priority, k)

            return new_key

    # 1. TimSort (usa el sorted() nativo de Python que utiliza TimSort)
    def tim_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        return sorted(arr, key=effective_key)

    # 2. Comb Sort
    def comb_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        n = len(arr)
        gap = n
        shrink = 1.3
        sorted_flag = False

        while not sorted_flag:
            gap = int(gap / shrink)
            if gap <= 1:
                gap = 1
                sorted_flag = True
            i = 0
            while i + gap < n:
                if effective_key(arr[i]) > effective_key(arr[i + gap]):
                    arr[i], arr[i + gap] = arr[i + gap], arr[i]
                    sorted_flag = False
                i += 1
        return arr

    # 3. Selection Sort
    def selection_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        for i in range(len(arr)):
            min_idx = i
            for j in range(i + 1, len(arr)):
                if effective_key(arr[j]) < effective_key(arr[min_idx]):
                    min_idx = j
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
        return arr

    # 4. Tree Sort (utilizando un árbol binario de búsqueda)
    class _TreeNode:
        def __init__(self, value):
            self.value = value
            self.left = None
            self.right = None

    def _insert_tree(self, root, value, effective_key):
        if root is None:
            return self._TreeNode(value)
        if effective_key(value) < effective_key(root.value):
            root.left = self._insert_tree(root.left, value, effective_key)
        else:
            root.right = self._insert_tree(root.right, value, effective_key)
        return root

    def _inorder_tree(self, root, result):
        if root:
            self._inorder_tree(root.left, result)
            result.append(root.value)
            self._inorder_tree(root.right, result)

    def tree_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        root = None
        for item in arr:
            root = self._insert_tree(root, item, effective_key)
        result = []
        self._inorder_tree(root, result)
        return result

    # 5. Pigeonhole Sort (para datos numéricos)
    def pigeonhole_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        # Se asume que los valores extraídos son numéricos
        values = [effective_key(x)[1] if isinstance(effective_key(x), tuple) else effective_key(x) for x in arr]
        min_val = min(values)
        max_val = max(values)
        size = max_val - min_val + 1

        # Crear "pigeonholes"
        holes = [[] for _ in range(size)]
        for item in arr:
            # Utiliza el valor numérico real (segundo elemento en la tupla si aplica)
            val = effective_key(item)
            if isinstance(val, tuple):
                actual_val = val[1]
            else:
                actual_val = val
            holes[actual_val - min_val].append(item)

        sorted_arr = []
        for hole in holes:
            sorted_arr.extend(hole)
        return sorted_arr

    # 6. Bucket Sort (para datos numéricos; asume distribución uniforme)
    def bucket_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        if not arr:
            return arr
        # Obtener valores numéricos, asumiendo que son numéricos
        values = [effective_key(x)[1] if isinstance(effective_key(x), tuple) else effective_key(x) for x in arr]
        min_val, max_val = min(values), max(values)
        bucket_count = len(arr)
        buckets = [[] for _ in range(bucket_count)]

        for item in arr:
            val = effective_key(item)
            if isinstance(val, tuple):
                actual_val = val[1]
            else:
                actual_val = val
            # Normalizar el índice
            norm_index = int(((actual_val - min_val) / (max_val - min_val + 1e-9)) * (bucket_count - 1))
            buckets[norm_index].append(item)

        sorted_arr = []
        for bucket in buckets:
            sorted_arr.extend(sorted(bucket, key=effective_key))
        return sorted_arr

    # 7. Quick Sort
    def quick_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        if len(arr) <= 1:
            return arr
        pivot = effective_key(arr[len(arr) // 2])
        left = [x for x in arr if effective_key(x) < pivot]
        middle = [x for x in arr if effective_key(x) == pivot]
        right = [x for x in arr if effective_key(x) > pivot]
        return self.quick_sort(left, key, search_value) + middle + self.quick_sort(right, key, search_value)

    # 8. Heap Sort
    def heap_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        import heapq
        heap = [(effective_key(x), x) for x in arr]
        heapq.heapify(heap)
        return [heapq.heappop(heap)[1] for _ in range(len(heap))]

    # 9. Bitonic Sort (asume longitud potencia de 2; se extiende la lista si es necesario)
    def bitonic_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)

        def compare_and_swap(a, i, j, direction):
            if (direction == 1 and effective_key(a[i]) > effective_key(a[j])) or \
                    (direction == 0 and effective_key(a[i]) < effective_key(a[j])):
                a[i], a[j] = a[j], a[i]

        def bitonic_merge(a, low, cnt, direction):
            if cnt > 1:
                k = cnt // 2
                for i in range(low, low + k):
                    compare_and_swap(a, i, i + k, direction)
                bitonic_merge(a, low, k, direction)
                bitonic_merge(a, low + k, k, direction)

        def _bitonic_sort(a, low, cnt, direction):
            if cnt > 1:
                k = cnt // 2
                _bitonic_sort(a, low, k, 1)
                _bitonic_sort(a, low + k, k, 0)
                bitonic_merge(a, low, cnt, direction)

        import math
        n = len(arr)
        power = 2 ** math.ceil(math.log2(n))
        extended = list(arr) + [arr[-1]] * (power - n)
        _bitonic_sort(extended, 0, power, 1)
        return extended[:n]

    # 10. Gnome Sort
    def gnome_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        index = 0
        while index < len(arr):
            if index == 0 or effective_key(arr[index]) >= effective_key(arr[index - 1]):
                index += 1
            else:
                arr[index], arr[index - 1] = arr[index - 1], arr[index]
                index -= 1
        return arr

    # 11. Binary Insertion Sort
    def binary_insertion_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)

        def binary_search(sub_arr, item, start, end):
            if start == end:
                return start if effective_key(item) < effective_key(sub_arr[start]) else start + 1
            if start > end:
                return start
            mid = (start + end) // 2
            if effective_key(item) == effective_key(sub_arr[mid]):
                return mid
            elif effective_key(item) < effective_key(sub_arr[mid]):
                return binary_search(sub_arr, item, start, mid - 1)
            else:
                return binary_search(sub_arr, item, mid + 1, end)

        for i in range(1, len(arr)):
            val = arr[i]
            j = binary_search(arr, val, 0, i - 1)
            arr = arr[:j] + [val] + arr[j:i] + arr[i + 1:]
        return arr

    # 12. Radix Sort (para números enteros no negativos)
    def radix_sort(self, arr, key=lambda x: x, search_value=None):
        # Para Radix Sort asumimos que los elementos son enteros no negativos;
        # el parámetro key se usa para extraer el valor numérico.
        effective_key = self._get_effective_key(key, search_value)

        def get_digit(n, d):
            return (n // 10 ** d) % 10

        values = [effective_key(x)[1] if isinstance(effective_key(x), tuple) else effective_key(x) for x in arr]
        if not values:
            return arr
        max_val = max(values)
        exp = 0
        output = list(arr)
        while 10 ** exp <= max_val:
            buckets = [[] for _ in range(10)]
            for item in output:
                # Obtener el valor numérico
                val = effective_key(item)
                actual_val = val[1] if isinstance(val, tuple) else val
                digit = get_digit(actual_val, exp)
                buckets[digit].append(item)
            output = [item for bucket in buckets for item in bucket]
            exp += 1
        return output

    # 13. Metodo Burbuja
    def bubble_sort(self, arr, key=lambda x: x, search_value=None):
        effective_key = self._get_effective_key(key, search_value)
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if effective_key(arr[j]) > effective_key(arr[j + 1]):
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr

