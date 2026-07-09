import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Divas paralēlas kolekcijas ar vienādiem slug: programma vieglajā valodā
// un oriģināls. Failus ģenerē scripts/generate_content.py.
const easy = defineCollection({
  loader: glob({ base: './src/content/easy', pattern: '**/*.md' }),
  schema: z.object({ title: z.string() }),
});

const orig = defineCollection({
  loader: glob({ base: './src/content/orig', pattern: '**/*.md' }),
  schema: z.object({ title: z.string() }),
});

export const collections = { easy, orig };
