import discord
from discord.ext import commands

from PIL import Image
from sklearn.cluster import KMeans
from sklearn.neighbors import KDTree
import logging, os, typing, urllib.request, math, functools, numpy

class KDNode:
    def __init__(self, key: (int,), key_idx: int, average: (int,)=None):
        # Key to compare by
        self.key = key
        # What dimension to compare by
        self.key_idx = key_idx
        # Average color of bucket
        self.average = average
        # Children
        self.left = None
        self.right = None

    def query(self, val: (int,)):
        # Return bucket average
        if self.is_leaf():
            return self.average

        if val[self.key_idx] < self.key[self.key_idx]:
            return self.left.query(val)
        return self.right.query(val)

    def is_leaf(self):
        return self.left is None and self.right is None

def construct_tree(pixels: [(int,)], depth_limit: int, depth: int=0):
    if not pixels:
        return None

    # Reached max depth for bucket
    if depth >= depth_limit:
        total = list(functools.reduce(lambda a, b: [_a + _b for _a, _b in zip(a, b)], pixels))
        average = tuple(v // len(pixels) for v in total)
        return KDNode(None, None, average)

    # Track best range
    ranges = [[255, 0] for i in range(3)]
    for p in pixels:
        for i in range(3):
            ranges[i][0] = min(ranges[i][0], p[i])
            ranges[i][1] = max(ranges[i][1], p[i])

    # Key dimension, best range
    best_range = (0, 0)
    for i in range(3):
        diff = ranges[i][1] - ranges[i][0]
        if diff > best_range[1]:
            best_range = (i, diff)

    # Sort on key
    rgb_key = best_range[0]
    pixels.sort(key=lambda x: x[rgb_key])

    # Split on key
    median_coord = len(pixels) // 2
    median = pixels[median_coord]
    root = KDNode(median, rgb_key)
    root.left = construct_tree(pixels[:median_coord], depth_limit, depth + 1)
    root.right = construct_tree(pixels[median_coord:], depth_limit, depth + 1)
    return root

class ImageExtension(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self._bot = bot

    def _parse_arguments(self, attachments: [discord.Attachment], args: [str], int_arg: int):
        if attachments:
            source = attachments[0]
            if args:
                try:
                    int_arg = int(args[0])
                except: pass
        elif args:
            source = args[0]
            try:
                int_arg = int(args[1])
            except: pass
        return source, int_arg

    async def _retrieve_image(self, source: typing.Union[discord.Attachment, str]):
        # Retrieve file to quantize
        quantize_fname = None
        if type(source) is discord.Attachment:
            attachment = source
            if attachment.height is not None:
                written = await attachment.save(open(attachment.filename, 'wb'))
                if written != attachment.size:
                    return (None, 'Unexpected error processing attachment, please try again.')
                else:
                    quantize_fname = attachment.filename
            else:
                return (None, 'Expected an image attachment but found something else')
        else:
            url = source
            if 'http' in url:
                if 'cdn.discordapp' in url:
                    return (None, 'Sorry, bots aren\'t allowed to access discord urls')
                else:
                    ext = url.split('.')[-1]
                    if ext not in ['png', 'jpg', 'jpeg', 'gif']:
                        return (None, 'Sorry, I only accept png, jpg, jpeg, and gif files')
                    quantize_fname = 'quantize.' + ext
                    try:
                        urllib.request.urlretrieve(url, quantize_fname)
                    except urllib.error.HTTPError as e:
                        return (None, 'There was an error retrieving the image from that url.')
            else:
                return (None, 'Missing image link or attachment')
        return (quantize_fname, 'Success')

    @commands.command(help='https://en.wikipedia.org/wiki/Image_segmentation')
    async def segment(self, ctx: commands.Context, *args: str):
        clusters = 8
        source, clusters = self._parse_arguments(ctx.message.attachments, args, clusters)

        segment_fname, status = await self._retrieve_image(source)
        if segment_fname is None:
            await ctx.send(status)

        if clusters not in [4, 8, 16]:
            await ctx.send('Sorry, the cluster needs to be 4, 8, or 16.')

        if segment_fname is not None:
            await ctx.send('Doing a thicc calculation, this may take a while...', delete_after=15)
            async with ctx.typing():
                logging.info('Segmenting image with {} clusters'.format(clusters))
                img = Image.open(segment_fname).convert('RGB')
                output = self._segment_image(img, clusters)
                output.save(segment_fname)
                await ctx.send(file=discord.File(segment_fname))

        # In case of error, cleanup file
        try:
            os.remove(segment_fname)
        except: pass

    def _segment_image(self, img: Image, clusters: int):
        MAX_DIM = (800, 600)
        if img.width > MAX_DIM[0] or img.height > MAX_DIM[1]:
            resize_ratio = min(MAX_DIM[0] / img.width, MAX_DIM[1] / img.height)
            new_size = (int(resize_ratio * img.width), int(resize_ratio * img.height))
            img = img.resize(new_size)
            print('Image was resized to ({}, {})'.format(*new_size))

        pixel_data = img.getdata()

        kmeans = KMeans(n_clusters=clusters)
        kmeans.fit(pixel_data)

        color_palette = list(map(lambda x: tuple(int(v) for v in x), kmeans.cluster_centers_))
        tree = KDTree(numpy.asarray(color_palette))
        output = Image.new(mode='RGB', size=(img.width, img.height))
        plist = list(map(lambda x: color_palette[tree.query([x], return_distance=False)[0][0]], pixel_data))
        output.putdata(plist)
        return output

    @commands.command(help='https://en.wikipedia.org/wiki/Color_quantization')
    async def quantize(self, ctx: commands.Context, *args: str):
        buckets = 4
        source, buckets = self._parse_arguments(ctx.message.attachments, args, buckets)

        quantize_fname, status = await self._retrieve_image(source)
        if quantize_fname is None:
            await ctx.send(status)

        # Calculate max depth of tree from number of buckets
        try:
            depth_limit = int(math.log2(buckets))
        except:
            depth_limit = 2 # log2 (4 color pallette)

        if quantize_fname is not None:
            await ctx.send('Doing a thicc calculation, this may take a while...', delete_after=15)
            async with ctx.typing():
                logging.info('Quantizing image with depth: ' + str(depth_limit))
                # Create KD-Tree of bit buckets
                img = Image.open(quantize_fname).convert('RGB')
                output = self._quantize_image(img, depth_limit)
                output.save(quantize_fname)
                await ctx.send(file=discord.File(quantize_fname))

        # In case of error, cleanup file
        try:
            os.remove(quantize_fname)
        except: pass

    def _quantize_image(self, img: Image, depth_limit: int):
        pixels = list(img.getdata())
        root = construct_tree(pixels, depth_limit)
        output = Image.new('RGB', (img.width, img.height))
        output.putdata(list(map(lambda x: root.query(x), img.getdata())))
        return output

def setup(bot: commands.Bot):
    logging.info('Setting up Image extension')
    bot.add_cog(ImageExtension(bot))
    logging.info('Done setting up Image extension')
