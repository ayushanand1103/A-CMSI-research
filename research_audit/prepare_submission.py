"""Prepare arXiv metadata from the approved manuscript; does not upload."""
from pathlib import Path
import json
import re
import unicodedata

root=Path(__file__).resolve().parents[1]
out=root/"outputs/robustness"; dest=out/"arxiv_submission"
source=(out/"manuscript/main.tex").read_text(encoding="utf-8")
confirmation=json.loads((dest/"author_confirmation.json").read_text())
assert confirmation["sole_author"] and confirmation["ai_assistance_disclosure_confirmed"]
title=re.search(r"\\title\{(.*?)\}\s*\\author",source,re.S).group(1)
title=" ".join(title.replace(r"\\"," ").replace("--","-").split())
abstract=source.split(r"\begin{abstract}",1)[1].split(r"\end{abstract}",1)[0]
abstract=" ".join(abstract.replace("--","-").split())
assert title.isascii() and abstract.isascii()
assert "no demonstrated predictive advantage" in abstract
assert not re.search(r"\bCHRIST\b",source)
for name,text in (("title.txt",title),("abstract.txt",abstract),("authors.txt","Ayush Anand (Independent researcher)")):
    (dest/name).write_text(text+"\n",encoding="utf-8")
comments="Robustness revision of research previously archived at Zenodo, doi:10.5281/zenodo.23682477."
(dest/"comments.txt").write_text(comments+"\n")
metadata=dict(title=title,authors=["Ayush Anand"],affiliation="Independent researcher",
              corresponding_email="ayushanand.1103@gmail.com",proposed_primary_category="q-fin.RM",
              license=confirmation["license"],license_url=confirmation["license_url"],
              author_declarations="explicitly_confirmed_by_author_2026-10-31",abstract=abstract,comments=comments,
              prior_research_doi="10.5281/zenodo.23682477",journal_reference=None,published_article_doi=None,
              arxiv_identifier=None,submission_status="not_submitted_no_authenticated_submission_connection",
              source_zip="../ACMSI_arXiv_Robustness_Source.zip",models_frozen=True)
(dest/"submission_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
(dest/"SUBMIT_TO_ARXIV.md").write_text("""# arXiv submission handoff

The author confirmed sole authorship, no external funding, no competing interests, and the AI disclosure on 31 October 2026. Institutional affiliation was removed as requested. License: **CC BY 4.0**. The model specifications and experimental results are frozen.

1. Sign in at https://arxiv.org/submit using your author account and start a new submission. If this work already has an arXiv identifier, use the replacement/version workflow instead; none was supplied here.
2. Upload `../ACMSI_arXiv_Robustness_Source.zip` and choose `main.tex` as the main file if requested. It contains the relative table/figure files, bibliography and generated `.bbl`. Use the LaTeX source ZIP, not just the locally compiled PDF.
3. Copy `title.txt`, `authors.txt`, `abstract.txt` and optional `comments.txt` into the corresponding fields. Proposed primary category: **q-fin.RM (Risk Management)**. Select **CC BY 4.0**. The prior Zenodo DOI is retained in the paper/comments; do not present it as a newly assigned arXiv ID or a journal-publication DOI.
4. Review arXiv's compiled preview, complete the author/account declarations, and finalize submission. Follow any account-specific endorsement prompt. Save the submission receipt/identifier.

No arXiv upload has occurred in this session: no authenticated arXiv submission connection was available. The account-side processing, endorsement and moderation outcome have not been represented as complete. Model optimization is not a remaining prerequisite.

Official guidance: https://info.arxiv.org/help/submit/index.html ; https://info.arxiv.org/help/submit_tex.html ; https://info.arxiv.org/help/license/index.html ; https://info.arxiv.org/help/prep.html
""",encoding="utf-8")
print("Submission metadata ready: Independent researcher; CC BY 4.0; author declarations confirmed; no upload performed.")
