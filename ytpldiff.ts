import { db } from './db';
import { diff } from './diff';
import { playlist } from './playlist';
import { property } from './0_property';
import { youtube } from './youtube_fetch';

const playlist_ids = property.define(
  'playlist_ids',
  ['LM'],
  (val): val is string[] =>
    Array.isArray(val) && val.every(v => typeof v === 'string')
);

export function diffAll(): void {
  const ids = playlist_ids.value;

  const database = db.open();
  const lastEntry = database.latest ?? {};
  const currentEntry: playlist.Collection = ids.reduce<{
    [id: string]: playlist.Item[];
  }>((m, pl) => {
    m[pl] = youtube.fetch(pl);
    return m;
  }, {});

  const diffs: { [playlistId: string]: diff.ItemDiff[] } = {};
  Object.entries(currentEntry).forEach(([id, items]) => {
    const d = diff.PlaylistItems(lastEntry[id] ?? [], items);
    if (d.length > 0) {
      diffs[id] = d;
    }
  });

  if (Object.keys(diffs).length > 0) {
    database.append(currentEntry);
    Logger.log(`diff found: ${JSON.stringify(diffs)}`);
    // TODO: Notify user
  }
}
