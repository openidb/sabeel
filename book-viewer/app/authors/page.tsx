"use client";

import { useState } from "react";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import catalog from "@/lib/catalog.json";

interface Book {
  id: string;
  title: string;
  titleLatin: string;
  author: string;
  authorLatin: string;
  datePublished: string;
  filename: string;
}

interface Author {
  name: string;
  nameLatin: string;
  bookCount: number;
  books: Book[];
}

export default function AuthorsPage() {
  const [searchQuery, setSearchQuery] = useState("");

  // Group books by author
  const authorsMap = (catalog as Book[]).reduce((acc, book) => {
    const key = book.author;
    if (!acc[key]) {
      acc[key] = {
        name: book.author,
        nameLatin: book.authorLatin,
        bookCount: 0,
        books: [],
      };
    }
    acc[key].bookCount++;
    acc[key].books.push(book);
    return acc;
  }, {} as Record<string, Author>);

  const authors = Object.values(authorsMap);

  const filteredAuthors = authors.filter((author) => {
    const query = searchQuery.toLowerCase();
    return (
      author.name.toLowerCase().includes(query) ||
      author.nameLatin.toLowerCase().includes(query)
    );
  });

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">Authors</h1>
        <Input
          type="text"
          placeholder="Search authors..."
          className="max-w-xs"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Books</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAuthors.length === 0 ? (
              <TableRow>
                <TableCell colSpan={2} className="text-center text-muted-foreground">
                  No authors found
                </TableCell>
              </TableRow>
            ) : (
              filteredAuthors.map((author) => (
                <TableRow key={author.name}>
                  <TableCell>
                    <div className="font-medium">{author.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {author.nameLatin}
                    </div>
                  </TableCell>
                  <TableCell>{author.bookCount}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <div className="mt-4 text-sm text-muted-foreground">
        Showing {filteredAuthors.length} of {authors.length} authors
      </div>
    </div>
  );
}
