"""Evaluate retrieved source-id ranking against teacher-adjudicated relevance.

CLI for trusted researchers only. Do not expose as a web endpoint.
Input CSV columns: case_id,query,relevant_source_ids (semicolon-separated),language,domain.
No accuracy values are fabricated; this script operates on adjudicated cases.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
from typing import Dict, List

from hybrid_rag import RAGIndex


def retrieval_metrics(found: List[str], relevant: List[str], k: int) -> Dict[str, float]:
    gold = set(str(item).strip() for item in relevant if str(item).strip())
    retrieved = list(dict.fromkeys(str(item) for item in found if str(item)))[:k]
    if not gold:
        raise ValueError("Each benchmark case requires at least one adjudicated relevant source")
    hits = [1 if item in gold else 0 for item in retrieved]
    dcg = sum(hit/math.log2(i+2) for i, hit in enumerate(hits))
    idcg = sum(1/math.log2(i+2) for i in range(min(k,len(gold))))
    return {
        "recall_at_k": sum(hits) / len(gold),
        "precision_at_k": sum(hits) / k,
        "ndcg_at_k": dcg / idcg if idcg else 0.0,
        "rr_at_k": (1.0 / (1 + hits.index(1))) if 1 in hits else 0.0,
    }


def run(gold_csv: Path, *, owner: str, project_id: int, index_path: Path, k: int) -> Dict:
    if not owner.strip() or project_id <= 0:
        raise ValueError("A valid researcher scope is mandatory")
    index = RAGIndex(index_path)
    rows = list(csv.DictReader(gold_csv.open(encoding='utf-8-sig',newline='')))
    if not rows:
        raise ValueError("Gold file contains no adjudicated cases")
    cases = []
    for row in rows:
        query = (row.get('query') or '').strip()
        expected = [x.strip() for x in (row.get('relevant_source_ids') or '').split(';') if x.strip()]
        if not query or not expected:
            raise ValueError(f"Incomplete gold case: {row.get('case_id','?')}")
        context = index.search(owner=owner,project_id=project_id,query=query,limit=k)
        ranked = list(dict.fromkeys(h['source_id'] for h in context.hits))
        measurements = retrieval_metrics(ranked,expected,k)
        cases.append({"case_id":row.get('case_id',''),"language":row.get('language',''),
                      "domain":row.get('domain',''),"retrieval_mode":context.retrieval_mode,
                      "diagnostic":context.retrieval_diagnostic,"retrieved":ranked,
                      "expected":expected,"metrics":measurements})
    names = ['recall_at_k','precision_at_k','ndcg_at_k','rr_at_k']
    macro={name:round(sum(c['metrics'][name] for c in cases)/len(cases),5) for name in names}
    return {"k":k,"n_cases":len(cases),"macro":macro,"cases":cases,
            "note":"Source-level ranking only; does not measure claim entailment or learning outcomes."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gold-csv',type=Path,required=True)
    parser.add_argument('--index',type=Path,required=True)
    parser.add_argument('--owner',required=True)
    parser.add_argument('--project-id',type=int,required=True)
    parser.add_argument('--k',type=int,default=6)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    # Evaluation should be reproducible and not unexpectedly call a cloud API.
    if os.getenv('RAG_CLOUD_EMBEDDINGS_ENABLED','false').lower() in {'true','1','yes'}:
        raise SystemExit('Cloud embeddings are enabled. Use an explicitly managed run after reviewing data permissions.')
    result=run(args.gold_csv,owner=args.owner,project_id=args.project_id,
               index_path=args.index,k=max(1,min(args.k,12)))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
