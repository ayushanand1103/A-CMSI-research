"""Validate the compiled PDF and assemble a self-contained arXiv source candidate."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import re
import shutil
import zipfile
from pypdf import PdfReader
import fitz


def package(root):
    root=Path(root); out=root/"outputs/robustness"; source=out/"manuscript"
    pdf=source/"main.pdf"; tex=source/"main.tex"
    reader=PdfReader(pdf)
    extracted="\n".join(p.extract_text() or "" for p in reader.pages)
    log=(source/"main.log").read_text(encoding="utf-8",errors="replace")
    bbl=(source/"main.bbl").read_text(encoding="utf-8")
    checks=dict(pdf_newer_than_source=pdf.stat().st_mtime>=tex.stat().st_mtime,
                valid_nonempty_pdf=len(reader.pages)>0,
                doi_preserved="10.5281/zenodo.23682477" in extracted,
                fourteen_original_references=all(re.search(r"\\bibitem(?:\[[\s\S]*?\])?\{"+key+r"\}",bbl) for key in
                    ("ciss","fimsis","engle","bollerslev","nelson","hamilton","pickands","mcneil","salhi","shannon","johansen","torrence","dm","hln")),
                no_unresolved_placeholders="@@" not in tex.read_text(encoding="utf-8"),
                no_undefined_citations="undefined citations" not in log.lower() and "citation" not in "\n".join(x for x in log.lower().splitlines() if "undefined" in x),
                no_undefined_references="undefined references" not in log.lower(),
                no_tex_error=not re.search(r"^! ",log,re.MULTILINE),
                no_overfull_boxes="Overfull \\hbox" not in log and "Overfull \\vbox" not in log)
    # Protect against a required file being omitted from the upload archive.
    inputs=re.findall(r"\\input\{([^}]+)\}",tex.read_text(encoding="utf-8"))
    graphics=re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}",tex.read_text(encoding="utf-8"))
    checks["all_relative_inputs_present"]=all((source/name).is_file() for name in inputs+graphics)
    rendered=fitz.open(pdf)
    fonts={font[0] for page in rendered for font in page.get_fonts()}
    checks["fonts_embedded"]=all(bool(rendered.extract_font(xref)[3]) for xref in fonts)
    files=[p for p in source.rglob("*") if p.is_file() and "preview" not in p.parts
           and (p.suffix in (".tex",".bib",".bbl",".png") or p.name=="README.md")]
    archive=out/"ACMSI_arXiv_Robustness_Source.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p,p.relative_to(source).as_posix())
    shutil.copy2(pdf,out/"ACMSI_arXiv_Robustness_Revision.pdf")
    status=dict(built_utc=datetime.now(timezone.utc).isoformat(),compiler="Tectonic 0.17.0 (XeTeX/BibTeX)",
                pages=len(reader.pages),bibliographic_entries=bbl.count("\\bibitem"),checks=checks,
                all_checks_pass=all(checks.values()),source_zip=str(archive.relative_to(root)),
                pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
                source_zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                source_files={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                submission="Not uploaded; author review/category/endorsement/licensing remain external")
    (source/"BUILD_STATUS.json").write_text(json.dumps(status,indent=2),encoding="utf-8")
    (source/"pdf_extracted_text.txt").write_text(extracted,encoding="utf-8")
    print(json.dumps(dict(pages=status["pages"],all_checks_pass=status["all_checks_pass"],checks=checks),indent=2))
    if not all(checks.values()):
        raise SystemExit("PDF/package readiness checks failed; see BUILD_STATUS.json")


if __name__=="__main__":
    package(Path(__file__).resolve().parents[1])
