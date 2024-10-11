#!/usr/bin/python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep, strftime
import pyautogui as pag
import argparse
import vlc
import os


class Screen:
    W = None
    H = None
    def __init__(self):
        pag.FAILSAFE = False
        self.W,self.H = pag.size()
    def snap(self, direction, delay = 0.25):
        pag.moveTo( int( self.W/10 ), int( self.H/2 ) )  # Click left screen, halfway down
        sleep( delay )
        pag.click()
        sleep( delay )
        if "L" in direction.upper():
            pag.hotkey("win","left")
        else: pag.hotkey("win","right")

class Environment:
    def __init__(self):
        self.screen = Screen()
    

class PageData:
    class F5:
        username = {"TB1": "guest@oceanpowertech.com",
                    "HWIL": "opt-testbed@fathom5.co",
                    "PB3-005": "dhs-user-owner@fathom5.co",
                    "TB2": None}
        password = {"TB1": "Guest!2022",
                    "HWIL": "Optuser2022!",
                    "PB3-005": "fantail!LANGUAGE7nonce2soften.contempt",
                    "TB2": None}
        title = "Maritime Domain Awareness Solution"
        idname = "username"
        pwname = "password"
        login = (By.CSS_SELECTOR,"button")
        #url = "https://staging-opt.fconnect.fathom5.io/login"
        url = "https://opt.fconnect.fathom5.io/login"
        desiredpos = "left"
        caveats = False
    class VF:
        username = "opt_user@outlook.com"
        password = "Ocean Power 1984!"
        title = "Log In - VesselFinder"
        idname = "email"
        pwname = "password"
        login = (By.CLASS_NAME,"field.cih")
        url = "https://www.vesselfinder.com/login"
        desiredpos = "right"
        caveats = True

def endRecord( player, instance ):
    player.stop()
    instance.release()

def screenRecord( fps = 20 ):
    dt = strftime("%d%b%Y_%H_%M_%S")
    path = f'/home/charlie/Videos/ScreenRecords/SeleniumTest_{dt}.mp4'
    print("Screen recording to output location: \n",path)
    if os.path.exists(path):
        print("Warning, path exists")
    instance = vlc.Instance()
    instance.log_unset()
    player = vlc.libvlc_media_player_new(instance)
    m = instance.media_new("screen://", ":screen-fps=24", ":sout=#transcode{vcodec=x264,vb=0,scale=0,acodec=mp4a,ab=128,channels=2,samplerate=44100}:file{dst=%s}" % path, ":sout-keep")
    player.set_media(m)
    player.play()
    return player, instance


def radarManip( driver, ac ):
    print("Not implemented yet")
    return driver


def videoManip( driver, ac, numPans = 5):
    sl = 0.5
    button = driver.find_element(By.XPATH,'//button[@title="Maximize"]')
    button.click( )
    sleep( sl )
    names = ("zoomIn","zoomOut","buttonLeft","buttonRight","buttonUp","buttonDown")
    buttons = [driver.find_element(By.CLASS_NAME, k) for k in names]
    count = 0
    for button in buttons:
        print(f"Testing optical camera {names[count]} {numPans} times...")
        for i in range(numPans):
            sleep( sl*5 )
            button.click()
        sleep( sl*5 )
        count+=1
    sleep( sl*5 )
    button = driver.find_element(By.XPATH,'//button[@title="Toggle Thermal"]')
    button.click( )
    sleep( sl )
    count = 0
    for button in buttons:
        print(f"Testing thermal camera {names[count]} {numPans} times...")
        for i in range(numPans):
            sleep( sl*5 )
            button.click()
        sleep( sl*5 )
        count+=1
    return driver


def mapManip(driver, ac, numZooms = 5, mapsettle = 30):
    for i in (1,2,3):
        sleep( mapsettle/3 )
        print(f"{mapsettle - i* mapsettle / 3}s remaining for map to localize.")
    print("Testing map functionality")
    geoMap = driver.find_element(By.ID,"map")
    scale = driver.find_element(By.CLASS_NAME,"leaflet-control-scale-line")
    sl = 1 
    print(f"1NM screen scale: {scale.size['width']}")
    ##### Zoom #################
    for elem,sl,command in zip ((driver.find_element(By.CLASS_NAME, 'leaflet-control-zoom-out'),
                                 driver.find_element(By.CLASS_NAME, 'leaflet-control-zoom-in')),
                                (2,2),
                                ("out","in")):
        i = 0
        print(f"Zoooming {command} {numZooms} times...")
        while i < numZooms:
            elem.click()
            sleep( sl )
            i+=1
    sl = 1.0  # Reduce sleep time for next tests
    ##### Polyline ##############
    print("Measuring distance")
    elem = driver.find_element(By.CLASS_NAME, 'leaflet-draw-draw-polyline')
    elem.click()
    sleep( sl )
    ac.move_to_element(geoMap).move_by_offset(60, 80).click().perform()
    ac.move_to_element(geoMap).move_by_offset(0, 0).click().perform()
    sleep( sl )
    ##### Draw ZOI ##########
    print("Creating zone of interest")
    elem = driver.find_element(By.CLASS_NAME, 'leaflet-draw-draw-polygon')
    elem.click()
    sleep( sl )
    for lat,lon in zip([100,100,-100,-100, 100],[100,-100,-100,100, 100]):
        ac.move_to_element(geoMap)
        sleep( sl )
        ac.move_to_element(geoMap).move_by_offset(lat, lon).click().perform()
        sleep( sl)
        ac.move_to_element(geoMap).move_by_offset(lat, lon)
    #----- ZOI Popup Window -----#
    elem = driver.find_element(By.XPATH,"//div[@title='#007F54']")
    elem.click()
    sleep( sl )
    elem = driver.find_element(By.NAME,'zoneName')
    elem.send_keys("SeleniumTZ")
    sleep( sl )
    elem = driver.find_element(By.CLASS_NAME,'zoi-button')
    elem.click()                           
    ##### Slew to pos ###########
    print("Slewing camera from map")
    sleep(sl)
    elem = driver.find_element(By.CLASS_NAME, 'leaflet-control-button.slew-btn')
    elem.click()
    for lat,lon in zip([100,100,-100,-100],[100,-100,-100,100]):
        ac.move_to_element(geoMap)
        sleep( sl*3 )
        ac.move_to_element(geoMap).move_by_offset(lat, lon).click().perform()
        sleep( sl)
    elem = driver.find_element(By.CLASS_NAME, "leaflet-slew-cancel.leaflet-slew-cancel-active")
    elem.click()
    sleep( sl )
    #### Delete layers ########
    print("Deleting layers")
    elem = driver.find_element(By.CLASS_NAME, "leaflet-draw-edit-remove")
    elem.click()
    sleep( sl )
    elem = driver.find_element(By.XPATH, "//a[@title='Clear all layers']")
    elem.click()
    print("Map functionality test complete.")
    return driver


def UIfunctionalChecks( driver ):
    ac = ActionChains(driver)
    for func in (mapManip, videoManip, radarManip):
    #for func in (videoManip, radarManip):
        driver = func( driver, ac )
        sleep( 2 )
    return driver


def login( driver, thisPage, env, asset = "TB1" ):
    driver.get( thisPage.url )
    env.screen.snap( thisPage.desiredpos )
    title = driver.title
    assert title == thisPage.title
    driver.implicitly_wait(0.5)
    user_box = driver.find_element(by=By.NAME, value= thisPage.idname)
    pswd_box = driver.find_element(by=By.NAME, value= thisPage.pwname)
    submit_button = driver.find_element(by = thisPage.login[0], value= thisPage.login[1])
    if isinstance(thisPage.username, dict):
        user_box.send_keys( thisPage.username[ asset ] )
        pswd_box.send_keys( thisPage.password[ asset ] )
    else:
        user_box.send_keys( thisPage.username )
        pswd_box.send_keys( thisPage.password )
    if thisPage.caveats:
        sleep( 6.0 )
        #driver.get( thisPage.url )
        #bt = driver.find_element(By.CLASS_NAME, "pprm_btn")
        #bt.click()
        #user_box = driver.find_element(by=By.NAME, value= thisPage.idname)
        #pswd_box = driver.find_element(by=By.NAME, value= thisPage.pwname)
        #user_box.send_keys( thisPage.username )
        #pswd_box.send_keys( thisPage.password )
        bt = driver.find_element(By.XPATH, '//*[@id="crb"]')
        bt.click()
        submit_button = driver.find_element(by = By.XPATH, value= '//*[@id="loginbtn"]')
    submit_button.click()
    return driver

    

def main( args, env, asset = "TB1" ):
    player,instance = screenRecord()
    driverA = webdriver.Chrome() #'/usr/local/chromedriver')
    sleep(0.5)
    driverA = login( driverA, PageData.F5, env, asset )
    sleep(1.5)
    driverA = UIfunctionalChecks( driverA )
    sleep(1.5)
    driverB = webdriver.Chrome()#'/usr/local/chromedriver')
    driverB = login( driverB, PageData.VF, env, asset)
    sleep(1.5)
    endRecord( player, instance )
    driverA.quit()
    driverB.quit()

def runFromLogger(asset):
    env = Environment()
    parser = argparse.ArgumentParser()
    parser.add_argument('-pw', '--password', default = None, help="Add password for F5 login")
    parser.add_argument("-i","--inPath", default = os.getcwd(),
                        help="inputPath to file, no entry defaults to first path matching $PWD/*.mpeg")
    parser.add_argument("-o","--outPath", default = os.getcwd(),
                        help="outputPath to write logging file, if enabled with -v, defaults to $PWD/output.log")
    parser.add_argument("-v","--verbose", action = "store_true", default = False, help="Enable additional logging")
    args = parser.parse_args()
    main( args, env, asset )

if __name__ == "__main__":
    print(__file__)
    env = Environment()
    parser = argparse.ArgumentParser()
    parser.add_argument('-pw', '--password', default = None, help="Add password for F5 login")
    parser.add_argument("-i","--inPath", default = os.getcwd(),
                        help="inputPath to file, no entry defaults to first path matching $PWD/*.mpeg")
    parser.add_argument("-o","--outPath", default = os.getcwd(),
                        help="outputPath to write logging file, if enabled with -v, defaults to $PWD/output.log")
    parser.add_argument("-v","--verbose", action = "store_true", default = False, help="Enable additional logging")
    args = parser.parse_args()
    main( args )



