"""작은 GLB 읽고 쓰기 (slim_heads.py가 animal-asset의 kaykit_swap 없이도 돌게).
G(path): .j(JSON) / acc(i) 숫자 배열 / add(arr, type, comp, target) 새 자료 / compact() 안 쓰는 자료 버리기 / save(path)"""
import json, struct
import numpy as np

COMP = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class G:
    def __init__(self, path):
        b = open(path, 'rb').read()
        l = struct.unpack('<I', b[12:16])[0]
        self.j = json.loads(b[20:20 + l])
        o = 20 + l
        bl = struct.unpack('<I', b[o:o + 4])[0]
        self.bin = bytearray(b[o + 8:o + 8 + bl])

    def acc(self, i):
        a = self.j['accessors'][i]; v = self.j['bufferViews'][a['bufferView']]
        dt = np.dtype(COMP[a['componentType']]); n = NC[a['type']]; cnt = a['count']
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', dt.itemsize * n)
        raw = np.frombuffer(bytes(self.bin), dtype=np.uint8, count=stride * (cnt - 1) + dt.itemsize * n, offset=off)
        out = np.lib.stride_tricks.as_strided(raw, shape=(cnt, dt.itemsize * n), strides=(stride, 1)).copy().view(dt).reshape(cnt, n)
        if a.get('normalized'):
            out = out.astype(np.float64) / np.iinfo(dt).max
        return out if n > 1 else out.reshape(-1)

    def add(self, arr, typ, comp, target=None, minmax=False):
        while len(self.bin) % 4: self.bin.append(0)
        raw = np.ascontiguousarray(arr).tobytes()
        v = {'buffer': 0, 'byteOffset': len(self.bin), 'byteLength': len(raw)}
        if target: v['target'] = target
        self.j['bufferViews'].append(v); self.bin.extend(raw)
        a = {'bufferView': len(self.j['bufferViews']) - 1, 'componentType': comp, 'count': int(arr.shape[0]), 'type': typ}
        if minmax:
            a['min'] = arr.min(0).astype(float).tolist(); a['max'] = arr.max(0).astype(float).tolist()
        self.j['accessors'].append(a)
        return len(self.j['accessors']) - 1

    def compact(self):
        j = self.j; used = set()
        for m in j.get('meshes', []):
            for p in m['primitives']:
                used.update(p['attributes'].values())
                if 'indices' in p: used.add(p['indices'])
                for t in p.get('targets', []): used.update(t.values())
        for s in j.get('skins', []):
            if 'inverseBindMatrices' in s: used.add(s['inverseBindMatrices'])
        for an in j.get('animations', []):
            for sm in an['samplers']: used.update((sm['input'], sm['output']))
        amap = {}; accs = []
        for i in sorted(used):
            amap[i] = len(accs); accs.append(j['accessors'][i])
        vused = sorted({a['bufferView'] for a in accs if 'bufferView' in a} | {im['bufferView'] for im in j.get('images', []) if 'bufferView' in im})
        nb = bytearray(); vmap = {}; views = []
        for vi in vused:
            v = dict(j['bufferViews'][vi]); s = v.get('byteOffset', 0)
            while len(nb) % 4: nb.append(0)
            chunk = self.bin[s:s + v['byteLength']]; v['byteOffset'] = len(nb); nb.extend(chunk)
            vmap[vi] = len(views); views.append(v)
        for a in accs:
            if 'bufferView' in a: a['bufferView'] = vmap[a['bufferView']]
        for im in j.get('images', []):
            if 'bufferView' in im: im['bufferView'] = vmap[im['bufferView']]
        f = lambda i: amap[i]
        for m in j.get('meshes', []):
            for p in m['primitives']:
                p['attributes'] = {k: f(v) for k, v in p['attributes'].items()}
                if 'indices' in p: p['indices'] = f(p['indices'])
                if 'targets' in p: p['targets'] = [{k: f(v) for k, v in t.items()} for t in p['targets']]
        for s in j.get('skins', []):
            if 'inverseBindMatrices' in s: s['inverseBindMatrices'] = f(s['inverseBindMatrices'])
        for an in j.get('animations', []):
            for sm in an['samplers']: sm['input'] = f(sm['input']); sm['output'] = f(sm['output'])
        j['accessors'] = accs; j['bufferViews'] = views; self.bin = nb

    def save(self, path):
        while len(self.bin) % 4: self.bin.append(0)
        self.j['buffers'] = [{'byteLength': len(self.bin)}]
        js = json.dumps(self.j, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
        open(path, 'wb').write(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(self.bin)) + struct.pack('<II', len(js), 0x4E4F534A) + js
                               + struct.pack('<II', len(self.bin), 0x004E4942) + bytes(self.bin))
