import { playlist } from './playlist';
import { property } from './0_property';
import { assert } from './1_util';

export namespace db {
  const database_drive_id = property.define<string | null>(
    'database_drive_id',
    null,
    (val: unknown): val is string | null =>
      val === null || typeof val === 'string'
  );
  export type Database = {
    append(items: playlist.Collection): void;
    readonly latest: playlist.Collection | null;
  };

  export function open(): Database {
    return new DatabaseImp(openDBFolder());
  }

  function createDBFolder(): string {
    const folder = Drive.Files?.insert({
      title: 'ytpldiff_db',
      mimeType: 'application/vnd.google-apps.folder',
    });
    if (folder?.id) {
      database_drive_id.set(folder.id);
      return folder.id;
    }
    throw new TypeError(`returned object have no id field: ${folder}`);
  }

  function openDBFolder(): string {
    const id = database_drive_id.value;
    if (id === null) {
      return createDBFolder();
    }
    try {
      Drive.Files?.get(id);
    } catch (err: unknown) {
      Logger.log('failed to fetch db folder:');
      Logger.log(err);
      if ((err as { details?: { code?: number } })?.details?.code === 404) {
        return createDBFolder();
      }
      throw err;
    }
    return id;
  }

  type RecordMetadata = {
    timestamp: Date;
    metadata: GoogleAppsScript.Drive.Schema.File;
  };

  class DatabaseImp {
    readonly id: string;
    metadata: RecordMetadata[];

    constructor(id: string) {
      this.id = id;
      this.metadata = [];

      let pageToken: undefined | string = undefined;
      do {
        const records: GoogleAppsScript.Drive.Schema.FileList = assert.notNull(
          Drive.Files?.list({
            q: `"${id}" in parents and trashed = false and mimeType = "application/vnd.google-apps.spreadsheet"`,
            maxResults: 100,
            pageToken: pageToken,
          })
        );

        if (records.items) {
          for (const record of records.items) {
            const timestamp = Date.parse(record.title ?? '');
            if (Number.isNaN(timestamp)) {
              Logger.log(`file name is not a time stamp: ${record.title}`);
              continue;
            }
            this.metadata.push({
              timestamp: new Date(timestamp),
              metadata: record,
            });
          }
        }
        pageToken = records.nextPageToken;
      } while (pageToken);
      // earlist first.
      this.metadata.sort(
        (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
      );
    }

    append(list: playlist.Collection): void {
      const timestamp = new Date(Date.now());
      const id = playlist.dump(list, timestamp);
      this.metadata.push({
        timestamp: timestamp,
        metadata: assert.notNull(
          Drive.Files?.patch({ parents: [{ id: this.id }] }, id, {
            fields: 'parents',
          })
        ),
      });
    }

    get latest(): playlist.Collection | null {
      if (this.metadata.length > 0) {
        return playlist.load(
          assert.notNull(this.metadata[this.metadata.length - 1].metadata.id)
        );
      }
      return null;
    }
  }
}
