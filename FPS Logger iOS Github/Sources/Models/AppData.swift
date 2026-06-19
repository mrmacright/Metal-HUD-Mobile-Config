import Foundation

enum AppData {

    // MARK: - Display Name Overrides
    static let displayRename: [String: String] = [
        "ShadowTrackerExtra":                      "PUBG MOBILE",
        "scimitar":                                "Assassin's Creed Mirage",
        "SolarlandClient":                         "Farlight 84",
        "hkrpg":                                   "Honkai: Star Rail",
        "bh3oversea":                              "Honkai Impact 3",
        "X6Game":                                  "Infinity Nikki",
        "ExtremeGame":                             "PUBG: New State",
        "librdr_1.50.60293175_ios-netflix_ww":     "Red Dead Redemption Netflix",
        "librdr_1.50.60293175_ios_ww":             "Red Dead Redemption",
        "WWE2K_Apple":                             "WWE 2K25: Netflix Edition",
        "narutoNext1":                             "NARUTO: Ultimate Ninja STORM",
        "Civ6_iOS64_Metal_FinalRelease":           "Civilization VI",
        "cobalt-tv":                               "Beach Buggy Racing 2",
        "OH2-IOS-Shipping":                        "Oceanhorn 3",
        "OH2-TVOS-Shipping":                       "Oceanhorn 3",
        "PrinceofPersiaTheLostCrown":              "Prince of Persia: The Lost Crown",
        "EasyDeliveryCo.":                         "Easy Delivery Co.",
        "SubwaySurf":                              "Subway Surfers",
        "FortniteClient-IOS-Shipping":             "Fortnite",
        "GenshinImpact":                           "Genshin Impact",
        "GRIDLegends":                             "GRID Legends",
        "TheDivision":                             "The Division Resurgence",
        "HacPro-IOS-Shipping":                     "Borderlands Mobile",
        "cod":                                     "Call of Duty: Mobile",
        "RainbowSixMobile":                        "Rainbow Six Mobile",
        "Endfield":                                "Arknights: Endfield",
        "HTGame-IOS-Shipping":                     "NTE: Neverness to Everness",
        "DeathStranding":                          "Death Stranding",
        "Hitman WOA":                              "HITMAN World of Assassination",
        "PESmobile":                               "eFootball",
        "SevenDeadlySins_Origin":                  "The Seven Deadly Sins: Origin",
        "BMI_Mobile":                              "Bright Memory: Infinite",
        "g112":                                    "Racing Master",
        "BASS2":                                   "Beyond a Steel Sky",
        "BlueysQuest":                             "Bluey's Quest",
        "braid":                                   "Braid, Anniversary Edition",
        "CivilizationVII":                         "Civilization VII",
        "CosmicShake":                             "SpongeBob: The Cosmic Shake",
        "DisneyDreamlightValley":                  "Disney Dreamlight Valley",
        "DRGSurvivor":                             "Deep Rock Galactic: Survivor",
        "fantasian":                               "Fantasian",
        "FIFAMobile":                              "EA SPORTS FC Mobile",
        "Gear.Club-Stradale":                      "Gear.Club - Stradale",
        "HorizonChase2":                           "Horizon Chase 2",
        "IsThisSeatTaken":                         "Is This Seat Taken?",
        "Mindcop2_3":                              "Mindcop",
        "SonicDreamTeam":                          "Sonic Dream Team",
        "thelastcompass":                          "The Last Campfire",
        "Trials_of_Mana":                          "Trials of Mana",
        "WayOfTheHunter":                          "Way of the Hunter",
        "OH2":                                     "Oceanhorn 2",
        "TABSPocketEdition":                       "TABS Pocket Edition",
        "BeyondBlue":                              "Beyond Blue",
        "EnterTheGungeon":                         "Enter The Gungeon",
        "ZenlessZoneZero":                         "Zenless Zone Zero",
        "librdr_1.58.63226194_ios-netflix_ww":     "Red Dead Redemption Netflix",
        "DeadCells":                               "Dead Cells",
        "JourneyLaunch":                           "Journey",
        "bully":                                   "Bully",
        "CatQuestIII":                             "Cat Quest III",
        "minecraftpe":                             "Minecraft",
        "FelicitysDoor":                           "Felicitys Door",
        "wildrift":                                "League of Legends: Wild Rift",
        "aces":                                    "War Thunder Mobile",
        "riftriff":                                "Rift Riff",
        "DarkRevival":                             "Bendy and the Dark Revival",
        "QRSL":                                    "Tower of Fantasy",
        "ctw":                                     "Grand Theft Auto: Chinatown Wars",
        "gtasa":                                   "Grand Theft Auto: San Andreas",
        "gta3vc":                                  "Grand Theft Auto: Vice City",
        "gta3aus":                                 "Grand Theft Auto III",
        "maxpayne":                                "Max Payne Mobile",
        "IslandersNewShores":                      "Islanders New Shores",
        "CultOfTheLamb":                           "Cult of the Lamb",
        "IAmYourBeast":                            "I Am Your Beast",
        "MonumentValley3":                         "Monument Valley 3",
        "PineHearts":                              "Pine Hearts",
        "PowerWashSimulator":                      "PowerWash Simulator",
        "SongsOfConquest":                         "Songs of Conquest",
        "SubnauticaBelowZero":                     "Subnautica: Below Zero",
        "CozyCaravan":                             "Cozy Caravan",
        "Arc-mobile":                              "Arcaea",
        "turnip2":                                 "Turnip Boy Robs a Bank",
        "Delta":                                   "Delta - Game Emulator",
        "Folium-iOS":                              "Folium",
        "RetroArchTV":                             "RetroArch",
    ]

    // MARK: - Metal HUD Support
    static let metalHUDSupported: Set<String> = [
        "scimitar", "ShadowTrackerExtra", "GenshinImpact", "cod", "GRIDLegends",
        "PrinceofPersiaTheLostCrown", "Endfield", "ZenlessZoneZero", "HTGame-IOS-Shipping",
        "DeathStranding", "EnterTheGungeon", "ExtremeGame", "narutoNext1",
        "Civ6_iOS64_Metal_FinalRelease", "cobalt-tv", "SubwaySurf",
        "FortniteClient-IOS-Shipping", "TheDivision", "HacPro-IOS-Shipping",
        "Hitman WOA", "PESmobile", "SevenDeadlySins_Origin", "BMI_Mobile",
        "g112", "BASS2", "BlueysQuest", "braid", "CivilizationVII", "CosmicShake",
        "DisneyDreamlightValley", "DRGSurvivor", "fantasian", "FIFAMobile",
        "Gear.Club-Stradale", "HorizonChase2", "IsThisSeatTaken", "Mindcop2_3",
        "SonicDreamTeam", "thelastcompass", "Trials_of_Mana", "WayOfTheHunter",
        "OH2", "OH2-IOS-Shipping", "OH2-TVOS-Shipping", "TABSPocketEdition",
        "BeyondBlue", "JourneyLaunch", "CatQuestIII", "minecraftpe",
        "RainbowSixMobile", "hkrpg", "bh3oversea", "X6Game", "EasyDeliveryCo.",
        "Wreckfest", "wildrift", "aces", "riftriff", "DarkRevival", "QRSL",
        "IslandersNewShores", "CultOfTheLamb", "IAmYourBeast", "MonumentValley3",
        "PineHearts", "PowerWashSimulator", "SongsOfConquest",
        // Display names for apps without aliased internal names
        "Resident Evil 2", "Resident Evil 3", "Resident Evil 4",
        "RESIDENT EVIL 7 biohazard", "Resident Evil Village for iOS",
        "Divinity: Original Sin 2", "Divinity Original Sin 2", "GRID Autosport",
        "Red Dead Redemption", "Red Dead Redemption Netflix", "Tomb Raider",
        "Alien Isolation", "Alien: Isolation", "NBA 2K26 Arcade Edition",
        "Company of Heroes", "XCOM 2 Collection", "DREDGE", "Unpacking",
        "PES Mobile", "The Division", "Dadish 3D", "Good Dadish", "Dadish 4",
        "Sniper Elite 4", "My Little Pony", "Clover Pit", "Roblox",
        "Hitman Absolution", "Lara Croft and the Guardian of Light",
        "Total War EMPIRE", "Subnautica", "SubnauticaBelowZero", "Wuthering Waves",
        "Control Ultimate Edition",
        "Cult of the Lamb", "Preserve", "Orlu", "Myst", "Felicitys Door",
        "INMOST", "POOLS", "Besiege", "Timelie", "Maneater", "Vohenn",
        "Thronefall", "TOEM", "Blasphemous", "Silt",
    ]

    static let metalHUDUnstable: Set<String> = [
        "RetroArch", "Delta", "ManicEmu", "PPSSPP", "Folium-iOS", "SideStore", "MeloNX",
    ]

    static let metalHUDUnsupported: Set<String> = [
        "gtasa", "gta3vc", "gta3aus", "maxpayne", "ctw", "SolarlandClient",
        "WWE2K_Apple", "DeadCells", "bully", "Arc-mobile", "turnip2",
        "Cassette Beasts", "Dead Cells", "Farlight 84", "WWE 2K25: Netflix Edition",
        "Bully", "Oceanhorn", "Bugsnax", "The Binding of Isaac Rebirth", "Phira",
    ]

    // MARK: - App Filter (non-gaming apps to hide)
    static let filterOut: Set<String> = [
        "Photos.app", "Weather.app", "VoiceMemos.app", "News.app", "Tips.app",
        "Reminders.app", "Music.app", "Maps.app", "Stocks.app", "AppStore.app",
        "Measure.app", "Magnifier.app", "Books.app", "Shortcuts.app", "Podcasts.app",
        "Calculator.app", "Health.app", "FindMy.app", "Freeform.app", "Camera.app",
        "AppleTV.app", "MobileCal.app", "MobileMail.app", "MobileSafari.app",
        "SequoiaTranslator.app", "MobileNotes.app", "MobileTimer.app", "MobileSMS.app",
        "Home.app", "Journal.app", "Files.app", "Fitness.app", "Passbook.app",
        "TestFlight.app", "FaceTime.app", "Image Playground.app", "Passwords.app",
        "Apple Store.app", "Contacts.app", "Preview.app", "Games.app",
        "Final Cut Camera.app", "maps.app", "Compass.app", "MobilePhone.app",
        "MobileStore.app",
        // Apple Watch
        "NanoPassbook.app", "NanoReminders.app", "WatchApp.app", "NanoTVRemote.app",
        "StarWarp WatchKit App.app", "NanoMusicRecognition.app", "NanoNowPlaying.app",
        "NanoMaps.app", "NanoMenstrualCycles.app", "NanoOxygenSaturation.app",
        "NanoSleep.app", "NanoStopwatch.app", "NanoTranslate.app",
        "WhatsAppWatchApp.app", "NanoNotes.app", "NanoMedications.app",
        "NanoMail.app", "NanoTimer.app", "NanoCalendar.app", "FindDevices.app",
        "NanoWorldClock.app", "NanoWeather.app", "Starbucks WatchKit App.app",
        "NanoAlarm.app", "NanoCalculator.app", "NanoCamera.app",
        "NanoHeartRhythm.app", "Mind.app", "FindItems.app", "HeartRate.app",
        "NanoHealthBalance.app", "Memoji.app", "SessionTrackerApp.app", "Urchin.app",
        // Storage
        "OneDrive.app", "Drive.app",
        // Productivity
        "Evernote.app", "Docs.app", "OneNote.app", "Word.app", "Sheets.app",
        "Acrobat.app", "Notion.app", "RunestoneEditor.app", "To Do.app", "Todoist.app",
        // Dictionary / Vocabulary
        "MyDictionary.app", "dictionary-ios.app", "Vocabulary.app",
        // Social / Messaging
        "Instagram.app", "Snapchat.app", "Facebook.app", "FaceBook.app",
        "Twitter.app", "Threads.app", "TikTok.app", "RedditApp.app",
        "LinkedIn.app", "narwhal2.app", "Messenger.app", "WhatsApp.app",
        "Discord.app", "Telegram.app", "Slack.app", "WeChat.app", "Zoom.app",
        "Meetup.app", "ElementX.app", "Signal.app", "Viber.app", "Pinterest.app",
        "TeamSpaceApp.app",
        // Video
        "YouTube.app", "YouTubeMusic.app", "YouTubeKids.app", "YouTubeCreator.app",
        "VLC for iOS.app", "Netflix.app", "DisneyPlus.app", "PrimeVideo.app",
        "Twitch.app", "ReelShort.app", "Crunchyroll.app", "Stan.app",
        "PPlusINTL.app", "Max-iOS.app",
        // Music
        "Spotify.app",
        // AI
        "GrokApp.app", "ChatGPT.app",
        // Editing
        "CapCut.app", "Adobe Photoshop.app", "Premiere.app", "Canva.app",
        // Email
        "Outlook-iOS.app", "Gmail.app",
        // Weather
        "WeatherPlus.app", "WeatherViewer.app",
        // Banking
        "CommBankProd.app", "Xero.app", "Coinbase.app", "Cash.app",
        "Paytm.app", "PayPal.app", "Cellopark.app", "Chase.app",
        // Fitness
        "Fitbit.app", "Strava.app", "Kubofit GLH Release.app", "Flo.app",
        // VPN
        "betternet.app", "ExpressVPN.app", "Free VPN.app", "HotspotShield.app",
        "IFV.app", "MullvadVPN.app", "NordVPN.app", "PlanetVPN.app",
        "ProtonVPN.app", "SuperVPN.app", "Surfshark.app", "TurboVPN.app",
        "vpn.app", "VPN.app", "VPNMaster.app", "X-VPN.app", "Betternet.app",
        "ProtonNative.app", "Tachyon.app",
        // Password Managers
        "Bitwarden.app", "SecureSignIn.app", "Authenticator.app",
        "Microsoft Authenticator.app", "1Password.app",
        // Dating
        "Tinder.app", "Hinge.app", "Bumble.app", "grindrx.app", "Yubo.app", "POF.app",
        // GPS Trackers
        "Life360.app",
        // Other
        "inoreader.app", "Aol.app", "BlackmagicCam.app", "LegoApp.app",
        "LegoBuilder.app", "Bridge.app", "Google.app", "Argo.app",
        "Dominguez.app", "Control Center.app", "Helix.app",
        "com.roborock.smart.app", "MintMobile.app", "GooglePhotos.app",
        "Geekbench 6.app", "HelloTalk_Binary.app", "Truecaller.app",
        "DMSS-GSA.app", "cpkamerasmart.app", "HikConnect.app", "TimeTree.app",
        "ActivityMonitorApp.app", "myID.iOS.app", "TeamTrack.app", "Dose.app",
        "TinCan.app", "Adobe Scan.app", "Amazon.app", "Meesho.app", "Depop.app",
        "eBay.app", "Flipkart.app", "Gumtree.app", "iAliexpress.app", "Shop.app",
        "Temu.app", "Wish.app", "ZZKKO.app",
    ]

    // MARK: - Icon Lookup
    static let appStoreIDs: [String: String] = [
        "Arc-mobile":                  "1205999125",
        "Delta":                       "1048524688",
        "Folium-iOS":                  "6498623389",
        "ShadowTrackerExtra":          "1330123510",
        "hkrpg":                       "1600525167",
        "GenshinImpact":               "1517783697",
        "FortniteClient-IOS-Shipping": "1261357853",
        "SubwaySurf":                  "512939461",
        "bh3oversea":                  "1394865141",
        "cod":                         "1287282214",
        "PESmobile":                   "1448228194",
        "ExtremeGame":                 "1542727626",
        "Endfield":                    "6737346616",
        "OH2":                         "1141837408",
        "OH2-IOS-Shipping":            "1539411904",
        "OH2-TVOS-Shipping":           "1539411904",
        "GRIDLegends":                 "6444311205",
        "Atlas":                       "1620883955",
        "Wreckfest":                   "1592505377",
        "Oceanhorn":                   "708196645",
        "JourneyLaunch":               "1445593893",
        "Divinity Original Sin 2":     "1458655678",
        "Tomb Raider":                 "6742988247",
        "minecraftpe":                 "479516143",
        "GRID Autosport":              "955951014",
        "aces":                        "1577525428",
        "QRSL":                        "1575728542",
        "gtasa":                       "763692274",
        "gta3vc":                      "578448682",
        "gta3aus":                     "479662730",
        "maxpayne":                    "512142109",
        "ctw":                         "344186162",
        "IslandersNewShores":          "6745312000",
        "WayOfTheHunter":              "6497948575",
        "RetroArchTV":                 "6499539433",
    ]

    static let localAppIcons: [String: String] = [
        "SideStore": "Sidestore.png",
        "MeloNX":    "MeloNX.png",
        "AltStore":  "AltStore.png",
    ]

    static let bundleIDs: [String: String] = [
        "Sniper Elite 4":   "com.rebellioninteractive.sniperelite4",
        "Tomb Raider":      "com.feralinteractive.tombraider",
        "GRID Autosport":   "com.feralinteractive.gridautosport",
        "Hitman Absolution": "com.feralinteractive.hitmanabsolution",
    ]

    /// Maps bundle IDs found in console log output to display names.
    /// Used to identify generic-named apps (e.g. "Client") at launch time.
    static let consoleBundleIDRenames: [String: String] = [
        "com.kurogame.wutheringwaves.global": "Wuthering Waves",
        "com.kurogame.wutheringwaves.cn":     "Wuthering Waves",
        "control-ios":                        "Control Ultimate Edition",
    ]

    static let skipIconLookup: Set<String> = [
        "App", "app", "APP", "Client", "Game", "game", "play", "PLAY", "GAME",
        "Gameface", "ios", "IOS", "iOS", "WM", "iPad", "iPhone", "client",
        "Mobile", "Player", "tvOS", "macOS", "Path", "path", "Atlas",
        "Pathless", "ShooterGame", "Runner", "runner", "UE4Game", "UE5Game",
        "UnrealGame", "TVOS-Shipping", "MacOS-Shipping", "IOS-Shipping",
        "Launcher", "launcher", "Main", "main", "watchOS", "visionOS",
        "AppleTV", "UnityPlayer", "Demo", "demo", "Test", "test",
    ]

    static let appIconSearchName: [String: String] = [
        "Tomb Raider": "Tomb Raider Remastered Feral Interactive",
    ]

    static let versionedAppDisplayNames: [String: String] = [
        "librdr_": "Red Dead Redemption",
    ]

    static let staleIconCache: Set<String> = [
        "Arc-mobile", "Delta", "Folium-iOS",
        "BASS2", "BlueysQuest", "braid", "CivilizationVII", "DisneyDreamlightValley",
        "DRGSurvivor", "fantasian", "FIFAMobile", "Game", "Gear.Club-Stradale",
        "GRIDLegends", "Gothic Classic", "HorizonChase2", "IsThisSeatTaken",
        "Mindcop2_3", "SonicDreamTeam", "thelastcompass", "Tomb Raider",
        "Trials_of_Mana",
        "App", "Atlas", "Client", "Gameface", "GRID Autosport", "ios",
        "Hitman Absolution", "minecraftpe", "OH2", "OH2-IOS-Shipping",
        "OH2-TVOS-Shipping", "Wreckfest", "Oceanhorn", "JourneyLaunch",
        "Divinity Original Sin 2", "aces", "QRSL", "gtasa", "gta3vc",
        "gta3aus", "maxpayne", "ctw", "IslandersNewShores", "WayOfTheHunter",
    ]

    // MARK: - Helpers
    static func metalHUDStatus(internal internalName: String, display displayName: String) -> (text: String, isPositive: Bool)? {
        if metalHUDSupported.contains(internalName) || metalHUDSupported.contains(displayName) {
            return ("Supports Metal HUD", true)
        }
        if metalHUDUnsupported.contains(internalName) || metalHUDUnsupported.contains(displayName) {
            return ("Metal HUD Unsupported", false)
        }
        if metalHUDUnstable.contains(internalName) || metalHUDUnstable.contains(displayName) {
            return ("Metal HUD May Not Work", false)
        }
        return nil
    }

    static func displayName(for internalName: String, liveDisplayNames: [String: String] = [:]) -> String {
        if let renamed = displayRename[internalName] { return renamed }
        if let live = liveDisplayNames[internalName] { return live }
        return internalName
    }
}
