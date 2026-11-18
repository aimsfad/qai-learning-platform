"""Trusted-operator CLI for 3alimnIA local RAG, not a public-user endpoint.

Example: python rag_cli.py add --project-id 5 --teacher professor --file references.pdf
Then:  python rag_cli.py approve --project-id 5 --teacher professor --source-id RAG...
"""
import argparse
import json

from hybrid_rag import open_index


def main() -> None:
    parser = argparse.ArgumentParser(description="3alimnIA local RAG document manager")
    parser.add_argument("command", choices=["add", "list", "approve", "revoke", "remove", "search"])
    parser.add_argument("--teacher", required=True, help="Exact owning teacher username (operator-only CLI)")
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--file", help="Input document for add")
    parser.add_argument("--origin", choices=["teacher", "external"], default="teacher")
    parser.add_argument("--license", default="")
    parser.add_argument("--source-id", help="Source ID for approve/revoke/remove")
    parser.add_argument("--query", help="Search query")
    args = parser.parse_args()
    index = open_index()
    shared = {"owner": args.teacher, "project_id": args.project_id}
    if args.command == "add":
        if not args.file:
            parser.error("add requires --file")
        result = index.add_document(**shared, path=args.file, origin=args.origin, license_note=args.license)
    elif args.command == "list":
        result = index.list_documents(**shared)
    elif args.command == "search":
        if not args.query:
            parser.error("search requires --query")
        hits = index.search(**shared, query=args.query)
        result = {"mode": hits.retrieval_mode, "sources": hits.source_ids, "hits": hits.hits}
    else:
        if not args.source_id:
            parser.error(f"{args.command} requires --source-id")
        result = (index.delete(**shared, source_id=args.source_id) if args.command == "remove"
                  else index.approve(**shared, source_id=args.source_id, approved=args.command == "approve"))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
