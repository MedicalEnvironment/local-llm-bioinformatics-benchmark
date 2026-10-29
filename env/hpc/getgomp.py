# Fetch Debian trixie libgomp1, verify SHA256 from the Packages index, extract libgomp.so.1* into argv[1].
import hashlib, io, lzma, sys, tarfile, urllib.request
M = "https://deb.debian.org/debian/"
pk = lzma.decompress(urllib.request.urlopen(M + "dists/trixie/main/binary-amd64/Packages.xz").read()).decode()
st = [s for s in pk.split("\n\n") if s.startswith("Package: libgomp1\n")][0]
f = dict(l.split(": ", 1) for l in st.splitlines() if ": " in l)
deb = urllib.request.urlopen(M + f["Filename"]).read()
assert hashlib.sha256(deb).hexdigest() == f["SHA256"], "checksum mismatch"
print(f["Filename"], "sha256 ok")
pos = 8
while pos < len(deb):  # ar archive members
    name = deb[pos:pos + 16].decode().strip().rstrip("/"); size = int(deb[pos + 48:pos + 58]); data = deb[pos + 60:pos + 60 + size]
    if name.startswith("data.tar"):
        with tarfile.open(fileobj=io.BytesIO(data)) as t:
            for m in t.getmembers():
                if "libgomp.so" in m.name:
                    m.name = m.name.split("/")[-1]; t.extract(m, sys.argv[1]); print("extracted", m.name)
    pos += 60 + size + (size % 2)
