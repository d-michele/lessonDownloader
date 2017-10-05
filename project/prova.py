
def main():
	videolessons_url = "https://elearning.polito.it/main/videolezioni/index.php?cidReq=2015_02MNOOA_0202558&id_session=0&gidReq=0&origin=&lp=1"
	prova = videolessons_url.split("/")

	print prova[2]
	
if __name__ == '__main__':
    main()