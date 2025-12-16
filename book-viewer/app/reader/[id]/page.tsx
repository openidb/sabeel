import { notFound } from "next/navigation";
import { EpubReader } from "@/components/EpubReader";
import catalog from "@/lib/catalog.json";

interface BookMetadata {
  id: string;
  title: string;
  titleLatin: string;
  author: string;
  authorLatin: string;
  datePublished: string;
  filename: string;
}

export function generateStaticParams() {
  return (catalog as BookMetadata[]).map((book) => ({
    id: book.id,
  }));
}

export default async function ReaderPage({
  params
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params;
  const bookMetadata = (catalog as BookMetadata[]).find(
    (b) => b.id === id
  );

  if (!bookMetadata) {
    notFound();
  }

  return <EpubReader bookMetadata={bookMetadata} />;
}
