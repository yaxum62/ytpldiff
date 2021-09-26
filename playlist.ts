import { assert } from './1_util';

export namespace playlist {
  const SHEET_TITLE_PREFIX = 'Playlist:';

  export type Collection = {
    readonly [id: string]: Item[];
  };

  export type Item = {
    readonly id: string;
    readonly videoId: string;
    readonly title: string;
    readonly description: string;
  };

  const ItemDescriptor: { [key: string]: 'string' } = {
    id: 'string',
    videoId: 'string',
    title: 'string',
    description: 'string',
  };

  function newDefaultItem(): Item {
    return {
      id: "",
      videoId: "",
      title: "",
      description: ""
    }
  }

  function isItem(candidate: unknown): candidate is Item {
    if (typeof candidate !== 'object' || candidate === null) {
      return false;
    }

    for (const [field, type] of Object.entries(ItemDescriptor)) {
      const value = (candidate as { [key: string]: unknown })[field];
      if (typeof value !== type) {
        Logger.log(`warning: unexpected type in column ${field}: ${candidate[field]}`);
        return false;
      }
    }
    return true;
  }

  function loadList(
    spreadsheetId: string,
    sheetTitle: string
  ): { id: string; items: Item[] } | null {
    if (!sheetTitle.startsWith(SHEET_TITLE_PREFIX)) {
      return null;
    }
    const playlistId = sheetTitle.slice(SHEET_TITLE_PREFIX.length);

    const range = assert.notNull(
      Sheets.Spreadsheets?.Values?.get(spreadsheetId, `'${sheetTitle}'`, {
        majorDimension: 'ROWS',
      })
    );
    if (!range.values || range.values.length === 0) {
      return null;
    }
    const header = range.values[0];
    const items: Item[] = [];
    range.values.forEach((row, idx) => {
      if (idx === 0) {
        return;
      }
      if (row.length > header.length) {
        throw new TypeError(`row ${idx + 1} too long in sheet ${sheetTitle}`);
      }
      const item: { [key: string]: unknown } = newDefaultItem();
      row.forEach((cell, c) => {
        item[header[c]] = cell;
      });
      if (isItem(item)) {
        items.push(item);
      } else {
        throw new TypeError(`unexpected value in row ${idx + 1}: ${item}`);
      }
    });
    return { id: playlistId, items: items };
  }

  export function load(spreadsheetId: string): Collection {
    const spreadsheetMetadata = assert.notNull(
      Sheets.Spreadsheets?.get(spreadsheetId, {
        fields: 'properties/title,sheets/properties/title',
      })
    );
    Logger.log(`Spreadsheet metadata: ${spreadsheetMetadata}`);

    const ret: { [id: string]: Item[] } = {};
    for (const sheet of spreadsheetMetadata.sheets ?? []) {
      const list = loadList(
        spreadsheetId,
        assert.notNull(sheet.properties?.title)
      );
      if (list) {
        ret[list.id] = list.items;
      }
    }
    return ret;
  }

  function valueToCellValue(
    val: unknown,
    spec: 'string'
  ): GoogleAppsScript.Sheets.Schema.ExtendedValue {
    if (spec === 'string') {
      return { stringValue: assert.string(val) };
    } else {
      throw new Error('unreachable');
    }
  }

  function objectoToRow(
    obj: { [key: string]: unknown },
    keys: string[],
    desc: { [key: string]: 'string' }
  ): GoogleAppsScript.Sheets.Schema.RowData {
    return {
      values: keys.map(key => ({
        userEnteredValue: valueToCellValue(obj[key], desc[key]),
      })),
    };
  }

  function listToSheet(
    sheetId: number,
    playlistId: string,
    items: Item[]
  ): GoogleAppsScript.Sheets.Schema.Sheet {
    const keys = Object.keys(ItemDescriptor);
    return {
      properties: {
        sheetId: sheetId,
        title: SHEET_TITLE_PREFIX + playlistId,
        gridProperties: {
          frozenRowCount: 1,
        },
      },
      data: [
        {
          startRow: 0,
          startColumn: 0,
          rowData: [
            {
              values: keys.map(key => ({
                userEnteredValue: { stringValue: key },
                userEnteredFormat: { textFormat: { bold: true } },
              })),
            },
          ],
        },
        {
          startRow: 1,
          startColumn: 0,
          rowData: items.map(item => objectoToRow(item, keys, ItemDescriptor)),
        },
      ],
      protectedRanges: [
        {
          range: {
            sheetId: sheetId,
          },
          warningOnly: true,
        },
      ],
    };
  }

  export function dump(collection: Collection, timestamp: Date): string {
    const spreadsheetId = assert.notNull(
      Sheets.Spreadsheets?.create({
        properties: {
          title: timestamp.toISOString(),
          defaultFormat: {
            numberFormat: {
              type: 'TEXT',
            },
          },
        },
        sheets: Object.entries(collection).map(([id, items], idx) =>
          listToSheet(idx, id, items)
        ),
      }).spreadsheetId
    );

    Sheets.Spreadsheets?.batchUpdate(
      {
        requests: Object.keys(collection).map(
          (_, idx): GoogleAppsScript.Sheets.Schema.Request => ({
            autoResizeDimensions: {
              dimensions: {
                sheetId: idx,
                dimension: 'COLUMNS',
              },
            },
          })
        ),
        includeSpreadsheetInResponse: false,
      },
      spreadsheetId
    );
    return spreadsheetId;
  }
}
