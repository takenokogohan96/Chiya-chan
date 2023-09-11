# coding: UTF-8

import discord
import asyncio
import datetime
import os
import configparser

from discord.ext import commands
from discord.ext import tasks
from text2wav import text2wav
#import config
import re

#config.ini読み出し
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')
token = config_ini.get('KEY', 'token')
version = config_ini.get('KEY', 'version')
commandrequest_channel = config_ini.getint('PARAM', 'commandrequest_channel')
max_length = config_ini.getint('PARAM', 'max_length')

#intents設定
intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='!',intents=intents)
bot.remove_command('help')
voice_client = None

print('\n　　／￣￣ヽ\n　 ＠/LLLL||\n　 卯|ﾟ‐ﾟﾉ|\n　 ﾉ／|Уﾘ＼\n　((L_F示|_/)\n　　　ﾋzz|\n　　　 ﾟ ﾟ　　🌸🌸')

def main():

    #入室コマンド
    @bot.command()
    async def join(ctx):

        #メッセージが書きこまれた箇所が、指定したテキストチャンネルのとき
        if ctx.channel.id == commandrequest_channel:
            dt_now = datetime.datetime.now()

            #コマンド発行者がVCに存在しない場合、VCに人がいないことを通告し無視する
            if ctx.author.voice is None:
                await ctx.send(f"{ctx.author.mention} ちゃんが（VCに）いないっ！！！")
                print('[JoinC]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「呼んだ人がVCにいなかったから接続を中止したわ」')
                return

            #VCに存在しないけどbotがボイスクライアントを持ってる場合、再起動を促す
            if not bot.guilds[0].voice_client is None and not bot.guilds[0].voice_client.is_connected():
                await ctx.send(f"{ctx.author.mention} ちゃん、私ちょっと混乱してるみたいだから`reset`で再起動してらえると助かるわ")
                print('[JoinC]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「呼ばれたけど私のボイスクライアントの情報が残ってるわ」') 
                return

            #すでにVCに接続状態である場合、分身できないことを通告し無視する
            if not bot.guilds[0].voice_client is None:
                await ctx.send(f"{ctx.author.mention} ちゃんよく見て！もうVCに接続してまーす！")
                print('[JoinC]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「呼ばれたけどもうVC接続状態だったわ」')
                return

            vc = ctx.author.voice.channel

            await vc.connect(reconnect=True)
            bellsource = discord.FFmpegPCMAudio("joinbell.wav")
            ctx.voice_client.play(bellsource)
            while ctx.voice_client.is_playing():
                await asyncio.sleep(0.1)
            source = discord.FFmpegPCMAudio(text2wav('ご注文は千夜ですか？'))
            ctx.voice_client.play(source)
            print('[JoinC]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「ボイスチャンネルに接続したわ」')

    #リセットコマンド
    @bot.command()
    async def reset(ctx):
        #メッセージが書きこまれた箇所が、指定したテキストチャンネルのとき
        if ctx.channel.id == commandrequest_channel:
            #すでにVCに接続状態である場合、正常な手順で切断する
            if not bot.guilds[0].voice_client is None:
                vc = bot.guilds[0].voice_client
                await vc.disconnect()
            os.startfile('chiya-chan.py')
            await ctx.send(f"{ctx.author.mention}ちゃんと過ごした日々を忘れない…！！（再起動が完了しました）")
            await bot.close()

    #テキストチャンネル設定コマンド
    @bot.command()
    async def set(ctx, message):
        try:
            setid = ctx.bot.get_channel(int(message))
            await setid.send(f"{ctx.author.mention} このチャンネルを読み上げるよう設定します")
        except:
            await ctx.send(f"{ctx.author.mention} ちゃんの指定したチャンネルが見つからないから、設定の変更を止めたわ")
            return
        
        # 変更をファイルに上書き保存
        config_ini.set('PARAM', 'commandrequest_channel', message)
        with open('config.ini', 'w') as configfile:
            config_ini.write(configfile)

        # 上書きした設定を再ロード
        global commandrequest_channel
        commandrequest_channel = config_ini.getint('PARAM', 'commandrequest_channel')
        
    #ヘルプ表示コマンド
    @bot.command()
    async def help(ctx):
        guild = bot.get_guild(ctx.guild.id)
        embed=discord.Embed(title="千夜ちゃんについて", description="こんにちは！ 読み上げBOTの千夜（ちや）です♪ 音声合成に私と同じ声の[VOICEROID](https://www.ah-soft.com/voiceroid/zunko/)を使っていて、[discord.py](https://discordpy.readthedocs.io/ja/latest/)で開発されたそうよ！\n\n機能：\n```・VCに接続、退室した人の名前を読み上げ\n・#" + guild.get_channel(commandrequest_channel).name + " の書き込みを読み上げ\n```",color=0x324c38)
        embed.set_thumbnail(url="https://i.imgur.com/3WWAaTM.png")
        embed.add_field(name="!join", value="VCに接続します", inline=True)
        embed.add_field(name="!reset", value="再起動します", inline=True)
        embed.add_field(name="!set [channel ID]", value="読み上げるテキストチャンネルを設定します", inline=False)
        embed.set_footer(text=version)
        await ctx.send(embed=embed)

    #起動部
    @bot.event
    async def on_ready():
        dt_now = datetime.datetime.now()
        await bot.change_presence(activity=discord.Game(f"!help"))
        print('[ready]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「私のバージョンは' + version + 'ね」')
        print('[ready]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「私のIDは' + str(bot.user.id) + 'よ」')
        print('[ready]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「ログイン完了したわ～」\n')
        auto_disconnection.start()

    # チャンネル入退室時の通知
    @bot.event
    async def on_voice_state_update(member, before, after):

        dt_now = datetime.datetime.now()
        #BOTがボイスクライアントを持ってる時だけ見るかつVCに存在するときだけ見る
        if not bot.guilds[0].voice_client is None and bot.guilds[0].voice_client.is_connected():
            #BOT以外の動きを見る
            if not member.id is bot.user.id:
                #チャンネルが移動した時だけ見る
                if not after.channel is before.channel:
                    #入室
                    if after.channel is bot.guilds[0].voice_client.channel:
                        #接続
                        if before.channel is None:
                            while bot.guilds[0].voice_client.is_playing():
                                await asyncio.sleep(0.1)
                            source = discord.FFmpegPCMAudio(text2wav(member.display_name + 'が参加しました！'))
                            bot.guilds[0].voice_client.play(source)
                            print('[state]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「' + member.display_name + 'の接続を呼び掛けたわ」')
                        #戻り
                        else:
                            while bot.guilds[0].voice_client.is_playing():
                                await asyncio.sleep(0.1)
                            source = discord.FFmpegPCMAudio(text2wav(member.display_name + 'が' + before.channel.name + 'から戻りました！'))
                            bot.guilds[0].voice_client.play(source)
                            print('[state]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「' + member.display_name + 'の別部屋からの戻りを呼び掛けたわ」')

                    #退室
                    elif before.channel is bot.guilds[0].voice_client.channel:
                        #切断
                        if after.channel is None:
                            while bot.guilds[0].voice_client.is_playing():
                                await asyncio.sleep(0.1)
                            source = discord.FFmpegPCMAudio(text2wav(member.display_name + 'が退室しました！'))
                            bot.guilds[0].voice_client.play(source)
                            print('[state]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「' + member.display_name + 'の退室を呼び掛けたわ」')
                        #移動
                        else:
                            while bot.guilds[0].voice_client.is_playing():
                                await asyncio.sleep(0.1)
                            source = discord.FFmpegPCMAudio(text2wav(member.display_name + 'が' + after.channel.name + 'に移動しました！'))
                            bot.guilds[0].voice_client.play(source)
                            print('[state]' + dt_now.strftime('[%m/%d %H:%M] ') + bot.user.name + '「' + member.display_name + 'の別部屋への移動を呼び掛けたわ」')

    #メッセージ受信の検知
    @bot.event
    async def on_message(message):

        #「<@」を探してメッセージにメンションが含まれている場合、ユーザ名に置換する
        if '<@' in message.content:     
            guild = bot.get_guild(message.guild.id)
            user_id_list = re.findall(r'@[0-9]{18}', message.content)
            user_id_list = list(map(lambda x: int(x.replace('@', '')), user_id_list))
            for user_id in user_id_list:
                user_nickname = guild.get_member(user_id).display_name
                message.content = message.content.replace('<@' + str(user_id) + '>', user_nickname) 

        #カスタム絵文字を無害化
        if re.search("<:\w+:(\d+)>", message.content):
            m = re.findall("<:\w+:(\d+)", message.content)
            for i in m:
                message.content = re.sub("<:\w+:(\d+)>","",message.content,1)

        #アニメーション絵文字を無害化
        if re.search("<a:\w+:(\d+)>", message.content):
            m = re.findall("<a:\w+:(\d+)", message.content)
            for i in m:
                message.content = re.sub("<a:\w+:(\d+)>","",message.content,1)

        #メッセージが書きこまれた箇所が、指定したテキストチャンネルのとき
        if message.channel.id == commandrequest_channel:
            #コマンドでないとき
            if not message.content.startswith('!'):
                # 喋っている途中は待つ
                if message.guild.voice_client:
                    while message.guild.voice_client.is_playing():
                        await asyncio.sleep(0.3)

                    #添付読み上げ部
                    if message.attachments:
                        for attachment in message.attachments:
                            if attachment.filename.lower().endswith(("png", "jpg", "jpeg", "gif", "webp")):
                                source = discord.FFmpegPCMAudio(text2wav("画像が貼られたわ。"))
                                message.guild.voice_client.play(source)
                            elif attachment.filename.lower().endswith(("txt")):
                                source = discord.FFmpegPCMAudio(text2wav("テキストファイルが送られたわ"))
                                message.guild.voice_client.play(source)
                            elif attachment.filename.lower().endswith(("zip", "rar", "7z")):
                                source = discord.FFmpegPCMAudio(text2wav("圧縮ファイルが送られたわ"))
                                message.guild.voice_client.play(source)
                            else:
                                extension_word = '.'.join(attachment.filename.lower().split('.')[1:])
                                source = discord.FFmpegPCMAudio(text2wav('ファイルが送られたわ。かくちょうしは「' + str(extension_word) + '」ね'))
                                message.guild.voice_client.play(source)

                    #URL読み上げ部
                    elif re.search('https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', message.content):
                        source = discord.FFmpegPCMAudio(text2wav('URLが書き込まれたわ。'))
                        message.guild.voice_client.play(source)

                    #通常読み上げ部
                    else:
                        #BOTがVCに存在してる時だけ読み上げる
                        if bot.guilds[0].voice_client.is_connected():
                            # 文字が長すぎると区切る
                            if len(message.content) > max_length:
                                message.content = "ツイッターより長い文は疲れるから読めないわ。"
                            message.content = message.content.replace('?', '？')
                            message.content = message.content.replace('/', '／')
                            source = discord.FFmpegPCMAudio(text2wav(message.content))
                            message.guild.voice_client.play(source)
                else:
                    pass
        await bot.process_commands(message)

    @tasks.loop(seconds=3)
    async def auto_disconnection():
        #BOTがボイスクライアントを持ってる時だけ見るかつVCに存在するときだけ確認
        if not bot.guilds[0].voice_client is None and bot.guilds[0].voice_client.is_connected():
            if len(bot.guilds[0].voice_client.channel.members) == 1:
                await bot.guilds[0].voice_client.disconnect()
                print('[state]VCが私一人だけになったから自動的に切断したわ')

    bot.run(token)

if __name__ == "__main__":
    main()
