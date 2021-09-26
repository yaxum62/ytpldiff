import { playlist } from './playlist';

export namespace diff {
    export type ItemDiff = {
        before: playlist.Item | null;
        after: playlist.Item | null;
    };

    function keyByVideoId(items: playlist.Item[]): { [id: string]: playlist.Item } {
        return items.reduce<{ [videoId: string]: playlist.Item }>((m, item) => {
            m[item.videoId] = item;
            return m;
        }, {});
    }

    export function PlaylistItems(
        before: playlist.Item[],
        after: playlist.Item[]
    ): ItemDiff[] {
        const beforeMap = keyByVideoId(before);
        const afterMap = keyByVideoId(after);

        const result: ItemDiff[] = [];
        Object.entries(beforeMap).forEach(([id, item]) => {
            if (!(id in afterMap)) {
                result.push({
                    before: item,
                    after: null,
                });
            }
        });
        Object.entries(afterMap).forEach(([id, item]) => {
            if (!(id in beforeMap)) {
                result.push({ before: null, after: item });
                return;
            }
            const beforeItem = beforeMap[id];
            if (
                beforeItem.description !== item.description ||
                beforeItem.title !== item.title ||
                beforeItem.id !== item.id
            ) {
                result.push({ before: beforeItem, after: item });
            }
        });
        return result;
    }
}
