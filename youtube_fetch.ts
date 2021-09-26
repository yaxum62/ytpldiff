import { playlist } from './playlist';
import { assert } from './1_util';

export namespace youtube {
    const MAX_PAGE_SIZE = 50;

    export function fetch(playlistId: string): playlist.Item[] {
        let result: playlist.Item[] = [];

        let nextPageToken: string | undefined = undefined;
        do {
            const resp: GoogleAppsScript.YouTube.Schema.PlaylistItemListResponse =
                assert.notNull(
                    YouTube.PlaylistItems?.list('snippet', {
                        playlistId: playlistId,
                        maxResults: MAX_PAGE_SIZE,
                        pageToken: nextPageToken,
                    })
                );
            Logger.log(`got ${resp?.items?.length} results`);
            result = result.concat(
                assert.notNull(
                    resp?.items?.map(
                        (item): playlist.Item => ({
                            id: assert.notNull(item.id),
                            videoId: assert.notNull(item.snippet?.resourceId?.videoId),
                            title: assert.notNull(item.snippet?.title),
                            description: assert.notNull(item.snippet?.description),
                        })
                    )
                )
            );
            nextPageToken = resp?.nextPageToken;
        } while (nextPageToken);
        return result;
    }
}
